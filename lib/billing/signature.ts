import { createHmac, timingSafeEqual } from "node:crypto";

/** Reject deliveries older than five minutes to limit replay. */
const TOLERANCE_SECONDS = 300;

export type SignatureResult =
  | { ok: true }
  | { ok: false; reason: "missing" | "malformed" | "expired" | "mismatch" };

/**
 * Verify `x-churnwise-signature: t=<unix seconds>,v1=<hex hmac>` where the HMAC-SHA256 is computed over
 * `${t}.${rawBody}` with the workspace's webhook secret.
 */
export function verifySignature(
  rawBody: string,
  header: string | null,
  secret: string,
  now = Date.now(),
): SignatureResult {
  if (!header) return { ok: false, reason: "missing" };
  const parts = Object.fromEntries(
    header.split(",").map((kv) => kv.trim().split("=", 2) as [string, string]),
  );
  const timestamp = Number(parts.t);
  if (!Number.isFinite(timestamp) || !parts.v1) return { ok: false, reason: "malformed" };
  if (Math.abs(now / 1000 - timestamp) > TOLERANCE_SECONDS) return { ok: false, reason: "expired" };

  const expected = createHmac("sha256", secret).update(`${timestamp}.${rawBody}`).digest();
  const received = Buffer.from(parts.v1, "hex");
  if (received.length !== expected.length || !timingSafeEqual(received, expected))
    return { ok: false, reason: "mismatch" };
  return { ok: true };
}
