/**
 * Smart retry schedule: when to try a failed charge again, based on why it failed. Hard declines skip
 * retries and go straight to a card-update request.
 */
export const MAX_ATTEMPTS = 4;

const HARD_DECLINES = new Set([
  "expired_card",
  "lost_card",
  "stolen_card",
  "incorrect_number",
  "authentication_required",
]);

/** Days to wait before each retry, by attempt number (1-based). */
const SOFT_SCHEDULE = [1, 3, 5, 7];
/** Insufficient funds recover best just after common paydays. */
const PAYDAYS = [1, 15];

export type RetryDecision =
  | { action: "retry"; at: Date }
  | { action: "request_card_update" }
  | { action: "give_up" };

function nextPayday(from: Date): Date {
  const d = new Date(from);
  for (let i = 1; i <= 31; i++) {
    d.setUTCDate(d.getUTCDate() + 1);
    if (PAYDAYS.includes(d.getUTCDate())) break;
  }
  d.setUTCHours(14, 0, 0, 0);
  return d;
}

export function nextRetry(declineCode: string, attempt: number, failedAt: Date): RetryDecision {
  if (HARD_DECLINES.has(declineCode)) return { action: "request_card_update" };
  if (attempt >= MAX_ATTEMPTS) return { action: "give_up" };
  if (declineCode === "insufficient_funds") return { action: "retry", at: nextPayday(failedAt) };
  const at = new Date(failedAt);
  at.setUTCDate(at.getUTCDate() + SOFT_SCHEDULE[attempt - 1]);
  return { action: "retry", at };
}
