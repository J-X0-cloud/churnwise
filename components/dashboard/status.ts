import type { CustomerStatus } from "@/types/revenue";

export type StatusTone = "good" | "ok" | "warn" | "bad";

export const STATUS_TONE: Record<CustomerStatus, StatusTone> = {
  Expanded: "good",
  Active: "ok",
  "At risk": "warn",
  "Past due": "warn",
  Downgraded: "warn",
  "Churn scheduled": "bad",
};

export const STATUS_GLYPH: Record<StatusTone, string> = { good: "↗", ok: "✓", warn: "!", bad: "✕" };
