/**
 * Webhook ingestion: store the raw event once (idempotent on its external id), then update the
 * projections it affects — customer MRR and MRR movements for subscription events, failed-payment
 * records for invoice events. Everything runs in one transaction so a retry never double-counts.
 */
import type { BillingSource, MovementType, Prisma } from "@prisma/client";

import { db } from "@/lib/db";
import { classifyMovement, monthlyValue } from "@/lib/revenue";
import type { Movement } from "@/types/revenue";

import type { BillingEvent, SubscriptionEvent } from "./events";
import { nextRetry } from "./retry-policy";

export type IngestResult =
  | { status: "processed"; eventId: string; movement: { type: Movement; amount: number } | null }
  | { status: "duplicate"; eventId: string }
  | { status: "unknown_workspace" };

const MOVEMENT_TYPE: Record<Movement, MovementType> = {
  new: "NEW",
  expansion: "EXPANSION",
  reactivation: "REACTIVATION",
  contraction: "CONTRACTION",
  churn: "CHURN",
};

const SOURCE: Record<BillingEvent["source"], BillingSource> = {
  stripe: "STRIPE",
  chargebee: "CHARGEBEE",
  recurly: "RECURLY",
  braintree: "BRAINTREE",
  paddle: "PADDLE",
  app_store: "APP_STORE",
  custom: "CUSTOM",
};

const toMajor = (minor: number) => minor / 100;

/** Normalised MRR a subscription contributes after this event. Canceled and paused subscriptions contribute nothing. */
export function subscriptionMrr(event: SubscriptionEvent): number {
  const { status, items } = event.data;
  if (
    event.type === "subscription.canceled" ||
    status === "canceled" ||
    status === "paused" ||
    status === "trialing"
  )
    return 0;
  return items.reduce(
    (sum, i) => sum + monthlyValue(toMajor(i.unitAmount), i.quantity, i.interval, i.intervalCount),
    0,
  );
}

async function applySubscription(
  tx: Prisma.TransactionClient,
  workspaceId: string,
  eventId: string,
  event: SubscriptionEvent,
) {
  const existing = await tx.customer.findUnique({
    where: { workspaceId_externalId: { workspaceId, externalId: event.data.customerId } },
  });
  const after = subscriptionMrr(event);
  const change = classifyMovement(
    existing ? { mrr: existing.mrr, previouslyChurned: existing.churnedAt !== null } : null,
    after,
  );

  const customer = await tx.customer.upsert({
    where: { workspaceId_externalId: { workspaceId, externalId: event.data.customerId } },
    create: {
      workspaceId,
      externalId: event.data.customerId,
      name: event.data.customerName,
      plan: event.data.plan,
      mrr: after,
      firstPaidAt: after > 0 ? event.occurredAt : null,
    },
    update: {
      name: event.data.customerName ?? undefined,
      plan: event.data.plan ?? undefined,
      mrr: after,
      firstPaidAt: existing?.firstPaidAt ?? (after > 0 ? event.occurredAt : null),
      churnedAt:
        after === 0 && (existing?.mrr ?? 0) > 0 ? event.occurredAt : after > 0 ? null : existing?.churnedAt,
    },
  });

  if (!change) return null;
  await tx.mrrMovement.create({
    data: {
      workspaceId,
      customerId: customer.id,
      eventId,
      type: MOVEMENT_TYPE[change.movement],
      amount: change.amount,
      mrrBefore: existing?.mrr ?? 0,
      mrrAfter: after,
      occurredAt: event.occurredAt,
    },
  });
  return { type: change.movement, amount: change.amount };
}

async function customerId(tx: Prisma.TransactionClient, workspaceId: string, externalId: string) {
  const customer = await tx.customer.upsert({
    where: { workspaceId_externalId: { workspaceId, externalId } },
    create: { workspaceId, externalId },
    update: {},
    select: { id: true },
  });
  return customer.id;
}

export async function ingestEvent(event: BillingEvent): Promise<IngestResult> {
  const workspace = await db.workspace.findUnique({ where: { slug: event.workspace }, select: { id: true } });
  if (!workspace) return { status: "unknown_workspace" };
  const workspaceId = workspace.id;

  return db.$transaction(async (tx) => {
    const seen = await tx.billingEvent.findUnique({
      where: { workspaceId_externalId: { workspaceId, externalId: event.id } },
      select: { id: true },
    });
    if (seen) return { status: "duplicate", eventId: seen.id } as const;

    const stored = await tx.billingEvent.create({
      data: {
        workspaceId,
        source: SOURCE[event.source],
        externalId: event.id,
        type: event.type,
        occurredAt: event.occurredAt,
        payload: event.data as Prisma.InputJsonValue,
      },
    });

    let movement: { type: Movement; amount: number } | null = null;

    switch (event.type) {
      case "subscription.created":
      case "subscription.updated":
      case "subscription.canceled":
        movement = await applySubscription(tx, workspaceId, stored.id, event);
        break;

      case "invoice.payment_failed": {
        const decision = nextRetry(event.data.declineCode, event.data.attempt, event.occurredAt);
        const fields = {
          attempts: event.data.attempt,
          declineCode: event.data.declineCode,
          status: decision.action === "give_up" ? ("LOST" as const) : ("OPEN" as const),
          nextRetryAt: decision.action === "retry" ? decision.at : null,
        };
        await tx.failedPayment.upsert({
          where: { workspaceId_invoiceExternalId: { workspaceId, invoiceExternalId: event.data.invoiceId } },
          create: {
            workspaceId,
            customerId: await customerId(tx, workspaceId, event.data.customerId),
            invoiceExternalId: event.data.invoiceId,
            amount: toMajor(event.data.amountDue),
            failedAt: event.occurredAt,
            ...fields,
          },
          update: fields,
        });
        break;
      }

      case "invoice.paid":
        // Only invoices that previously failed are recoveries; ordinary payments leave no projection.
        await tx.failedPayment.updateMany({
          where: { workspaceId, invoiceExternalId: event.data.invoiceId, status: "OPEN" },
          data: { status: "RECOVERED", recoveredAt: event.occurredAt, nextRetryAt: null },
        });
        break;
    }

    await tx.billingEvent.update({ where: { id: stored.id }, data: { processedAt: new Date() } });
    return { status: "processed", eventId: stored.id, movement } as const;
  });
}
