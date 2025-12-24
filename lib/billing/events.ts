import { z } from "zod";

/** Billing events as delivered by Churnwise connectors, normalised across Stripe, Chargebee, Recurly and others. */
const Source = z.enum(["stripe", "chargebee", "recurly", "braintree", "paddle", "app_store", "custom"]);

const SubscriptionItem = z.object({
  priceId: z.string(),
  /** Minor units (cents). */
  unitAmount: z.number().int().nonnegative(),
  quantity: z.number().int().positive().default(1),
  interval: z.enum(["day", "week", "month", "year"]),
  intervalCount: z.number().int().positive().default(1),
});

const Base = z.object({
  id: z.string().min(1),
  workspace: z.string().min(1),
  source: Source,
  occurredAt: z.coerce.date(),
});

const SubscriptionData = z.object({
  subscriptionId: z.string(),
  customerId: z.string(),
  customerName: z.string().optional(),
  plan: z.string().optional(),
  status: z.enum(["trialing", "active", "past_due", "paused", "canceled"]),
  currency: z.string().length(3),
  items: z.array(SubscriptionItem),
});

export const BillingEventSchema = z.discriminatedUnion("type", [
  Base.extend({ type: z.literal("subscription.created"), data: SubscriptionData }),
  Base.extend({ type: z.literal("subscription.updated"), data: SubscriptionData }),
  Base.extend({ type: z.literal("subscription.canceled"), data: SubscriptionData }),
  Base.extend({
    type: z.literal("invoice.payment_failed"),
    data: z.object({
      invoiceId: z.string(),
      customerId: z.string(),
      amountDue: z.number().int().positive(),
      attempt: z.number().int().positive(),
      declineCode: z.string(),
    }),
  }),
  Base.extend({
    type: z.literal("invoice.paid"),
    data: z.object({
      invoiceId: z.string(),
      customerId: z.string(),
      amountPaid: z.number().int().nonnegative(),
    }),
  }),
]);

export type BillingEvent = z.infer<typeof BillingEventSchema>;
export type SubscriptionEvent = Extract<BillingEvent, { type: `subscription.${string}` }>;
