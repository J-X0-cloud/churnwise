import { NextResponse } from "next/server";
import { z } from "zod";

import { BillingEventSchema } from "@/lib/billing/events";
import { ingestEvent } from "@/lib/billing/ingest";
import { verifySignature } from "@/lib/billing/signature";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * POST /api/webhooks/billing — receives normalised billing events from connectors.
 *
 * 401 on a bad signature, 400 on an invalid payload, 404 for an unknown workspace, 200 otherwise
 * (including duplicates, so the sender stops retrying).
 */
export async function POST(request: Request) {
  const secret = process.env.BILLING_WEBHOOK_SECRET;
  if (!secret) {
    return NextResponse.json({ error: "webhook_secret_not_configured" }, { status: 500 });
  }

  const rawBody = await request.text();
  const signature = verifySignature(rawBody, request.headers.get("x-churnwise-signature"), secret);
  if (!signature.ok) {
    return NextResponse.json({ error: "invalid_signature", reason: signature.reason }, { status: 401 });
  }

  let json: unknown;
  try {
    json = JSON.parse(rawBody);
  } catch {
    return NextResponse.json({ error: "invalid_json" }, { status: 400 });
  }

  const parsed = BillingEventSchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "invalid_event", issues: z.treeifyError(parsed.error) },
      { status: 400 },
    );
  }

  const result = await ingestEvent(parsed.data);
  if (result.status === "unknown_workspace") {
    return NextResponse.json({ error: "unknown_workspace" }, { status: 404 });
  }
  return NextResponse.json({ received: true, ...result });
}
