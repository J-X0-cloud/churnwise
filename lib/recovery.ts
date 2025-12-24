/** Failed-payment recovery: monthly outcomes and the 12-month funnel from failed charge to recovered or lost. */
import { monthLabel } from "@/lib/dates";
import { AMBER, BRAND, INK, MINT, RED } from "@/lib/palette";
import { MONTHS } from "@/lib/revenue";
import { DAILY } from "@/lib/data/simulation";
import type { FunnelItem, MonthlyRecovery } from "@/types/revenue";

/** Share of recovered revenue won back by retries alone (the rest by emails and card updates). */
const RETRY_SHARE = 0.57;
/** Share of failed revenue still inside its recovery window. */
const IN_RECOVERY_SHARE = 0.05;

const sum = (key: "failed" | "recovered", from: number, to?: number) =>
  DAILY.slice(from, to).reduce((a, r) => a + r[key], 0);

export function recoveryByMonth(months = 12): MonthlyRecovery[] {
  return MONTHS.slice(-months).map((m) => ({
    label: monthLabel(m.start, m.start.getMonth() === 0),
    failed: sum("failed", m.from, m.to),
    recovered: sum("recovered", m.from, m.to),
  }));
}

export interface RecoveryFunnel {
  items: FunnelItem[];
  failed: number;
  recovered: number;
  rate: number;
}

export function recoveryFunnel(): RecoveryFunnel {
  const failed = sum("failed", -365);
  const recovered = sum("recovered", -365);
  const retries = recovered * RETRY_SHARE;
  const pending = failed * IN_RECOVERY_SHARE;
  return {
    failed,
    recovered,
    rate: (recovered / failed) * 100,
    items: [
      { label: "Failed charges", value: failed, color: INK },
      { label: "Recovered by smart retries", value: retries, color: BRAND },
      { label: "Recovered by emails & card updates", value: recovered - retries, color: MINT },
      { label: "Still in recovery", value: pending, color: AMBER },
      { label: "Lost to involuntary churn", value: failed - recovered - pending, color: RED },
    ],
  };
}

/** Involuntary churn: failed revenue that was never recovered, as a monthly share of MRR. */
export function involuntaryChurnRate(): number {
  const { failed, recovered } = recoveryFunnel();
  const mrrDays = DAILY.slice(-365).reduce((a, r) => a + r.mrr, 0);
  return (((failed - recovered) * (1 - IN_RECOVERY_SHARE)) / mrrDays) * 30.4 * 100;
}
