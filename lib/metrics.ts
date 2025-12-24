/**
 * Metrics service for the dashboards: KPI tiles with deltas and sparklines, headline series, plan mix
 * and account trends. Built on lib/revenue (movement math) and the daily model.
 */
import { dayLabel, longDate, monthLabel } from "@/lib/dates";
import { money, num, pct, signedMoney, wholeDollars } from "@/lib/format";
import { BLUE, BRAND, MINT, RED } from "@/lib/palette";
import { createRng, lerp } from "@/lib/random";
import { involuntaryChurnRate, recoveryByMonth, recoveryFunnel } from "@/lib/recovery";
import { MONTHS, RANGES, grrAt, nrrAt, rangeStats, trailingChurnRate } from "@/lib/revenue";
import { CUSTOMERS } from "@/lib/data/customers";
import { PLANS } from "@/lib/data/plans";
import { DAILY, DAY_COUNT, LAST } from "@/lib/data/simulation";
import type { LinePoint } from "@/types/charts";
import type {
  CustomerAccount,
  DailyRevenue,
  Delta,
  Kpi,
  PlanRow,
  RangeKey,
  RangeStats,
} from "@/types/revenue";

// ------------------------------------------------------------------ deltas

export function delta(
  current: number,
  prior: number | null,
  { goodUp = true, unit = "%" }: { goodUp?: boolean; unit?: "%" | "pts" } = {},
): Delta | null {
  if (prior === null || prior === 0) return null;
  const change = unit === "pts" ? current - prior : ((current - prior) / Math.abs(prior)) * 100;
  const sign = change >= 0 ? "+" : "−";
  return {
    text: `${sign}${Math.abs(change).toFixed(1)}${unit === "pts" ? " pts" : "%"}`,
    arrow: change >= 0 ? "up" : "down",
    tone: change >= 0 === goodUp ? "good" : "bad",
  };
}

const note = (text: string): Delta => ({ text, tone: "neutral" });

// ------------------------------------------------------------------ series helpers

/** Sample a daily field across a range at ~24 points for sparklines. */
function sampled(from: number, pick: (r: DailyRevenue, i: number) => number): number[] {
  const step = Math.max(1, Math.floor((DAY_COUNT - from) / 24));
  const out: number[] = [];
  for (let i = from; i < DAY_COUNT; i += step) out.push(pick(DAILY[i], i));
  return out;
}

const trailing30 = (key: "recovered", i: number) =>
  DAILY.slice(Math.max(0, i - 30), i + 1).reduce((a, r) => a + r[key], 0);

/** Headline MRR line: month labels at month starts for 12M/24M, day labels otherwise. */
export function mrrLine(stats: RangeStats): LinePoint[] {
  const monthly = RANGES[stats.range].bucket === "month";
  return stats.line.map(({ date, value }) => ({
    label: monthly ? (date.getDate() <= 7 ? monthLabel(date, date.getMonth() === 0) : "") : dayLabel(date),
    tip: longDate(date),
    value,
  }));
}

/** Label spacing for the headline chart so labels never collide. */
export const MRR_LABEL_EVERY: Record<RangeKey, number> = { "30d": 5, "90d": 14, "12m": 1, "24m": 1 };

// ------------------------------------------------------------------ KPI tiles

export function overviewKpis(range: RangeKey): Kpi[] {
  const st = rangeStats(range);
  const s = st.start;
  const { comparisonNote } = RANGES[range];
  const or = (d: Delta | null, fallback: string) => d ?? note(fallback);

  return [
    {
      label: "MRR",
      value: money(st.mrr),
      hint: "Monthly recurring revenue, normalized from every active subscription",
      delta: or(delta(st.mrr, st.mrrStart), comparisonNote),
      spark: sampled(s, (r) => r.mrr),
    },
    {
      label: "Net new MRR",
      value: signedMoney(st.netNew),
      hint: "New + expansion + reactivation − contraction − churn",
      delta: or(delta(st.netNew, st.netNewPrior), comparisonNote),
      spark: sampled(s, (r, i) => r.mrr - DAILY[Math.max(0, i - 30)].mrr),
      sparkColor: MINT,
    },
    {
      label: "Net revenue retention",
      value: pct(st.nrr),
      hint: "Trailing 12 months, existing customers only",
      delta: or(delta(st.nrr, st.nrrStart, { unit: "pts" }), comparisonNote),
      spark: sampled(s, (_, i) => nrrAt(i)),
      sparkColor: BLUE,
    },
    {
      label: "Revenue churn",
      value: pct(st.churnRate, 2),
      unit: "/mo",
      hint: "Churned + contracted MRR as a share of MRR",
      delta: or(delta(st.churnRate, st.churnRatePrior, { goodUp: false, unit: "pts" }), "avg. per month"),
      spark: sampled(s, (_, i) => trailingChurnRate(i)),
      sparkColor: RED,
    },
    {
      label: "Customers",
      value: num(st.customers),
      delta: or(delta(st.customers, st.customersStart), comparisonNote),
      spark: sampled(s, (r) => r.customers),
    },
    {
      label: "ARPA",
      value: wholeDollars(st.arpa),
      hint: "Average revenue per account",
      delta: or(delta(st.arpa, st.arpaStart), comparisonNote),
      spark: sampled(s, (r) => r.arpa),
    },
    {
      label: "Customer LTV",
      value: money(st.ltv),
      hint: "ARPA × 82% gross margin ÷ logo churn",
      delta: or(delta(st.ltv, st.ltvStart), comparisonNote),
      spark: sampled(s, (r) => r.arpa),
      sparkColor: BLUE,
    },
    {
      label: "Recovered revenue",
      value: money(st.recovered),
      hint: "Failed payments won back by retries, emails and card updates",
      delta: or(delta(st.recovered, st.recoveredPrior), `${st.recoveryRate.toFixed(0)}% of failed`),
      spark: sampled(s, (_, i) => trailing30("recovered", i)),
      sparkColor: MINT,
    },
  ];
}

/** Trailing-12-month NRR and GRR at each of the last twelve month ends. */
export function retentionSeries(): { labels: string[]; nrr: number[]; grr: number[] } {
  const months = MONTHS.slice(-12);
  return {
    labels: months.map((m) => monthLabel(m.start, m.start.getMonth() === 0)),
    nrr: months.map((m) => nrrAt(m.to - 1)),
    grr: months.map((m) => grrAt(m.to - 1)),
  };
}

export function retentionKpis(): Kpi[] {
  const series = retentionSeries();
  return [
    {
      label: "Net revenue retention",
      value: pct(nrrAt(LAST)),
      delta: delta(nrrAt(LAST), nrrAt(LAST - 365), { unit: "pts" })!,
      spark: series.nrr,
      sparkColor: BLUE,
    },
    {
      label: "Gross revenue retention",
      value: pct(grrAt(LAST)),
      delta: delta(grrAt(LAST), grrAt(LAST - 365), { unit: "pts" })!,
      spark: series.grr,
      sparkColor: RED,
    },
    {
      label: "Logo churn",
      value: "1.74%",
      unit: "/mo",
      delta: { text: "−0.21 pts", arrow: "down", tone: "good" },
    },
    {
      label: "Median customer lifetime",
      value: "38 mo",
      delta: { text: "+4 mo", arrow: "up", tone: "good" },
    },
  ];
}

export function customerKpis(): Kpi[] {
  const now = DAILY[LAST].customers;
  const pastDue = 5070;
  return [
    {
      label: "Paying customers",
      value: num(now),
      delta: delta(now, DAILY[LAST - 30].customers)!,
      spark: DAILY.slice(-90)
        .filter((_, i) => i % 3 === 0)
        .map((r) => r.customers),
    },
    { label: "At risk", value: "41", delta: { text: "+6", arrow: "up", tone: "bad" } },
    { label: "Past due", value: "6", delta: note(`${money(pastDue)} MRR`) },
    { label: "Expanded this month", value: "58", delta: { text: "+9", arrow: "up", tone: "good" } },
  ];
}

export function recoveryKpis(): Kpi[] {
  const funnel = recoveryFunnel();
  const months = recoveryByMonth(12);
  return [
    {
      label: "Recovered (12 mo)",
      value: money(funnel.recovered),
      delta: { text: "+14.2%", arrow: "up", tone: "good" },
      spark: months.map((m) => m.recovered),
      sparkColor: MINT,
    },
    {
      label: "Recovery rate",
      value: pct(funnel.rate),
      delta: { text: "+3.8 pts", arrow: "up", tone: "good" },
      spark: months.map((m) => (m.recovered / m.failed) * 100),
      sparkColor: BRAND,
    },
    { label: "In recovery now", value: "$5.07k", delta: note("6 invoices") },
    {
      label: "Involuntary churn",
      value: pct(involuntaryChurnRate(), 2),
      unit: "/mo",
      delta: { text: "−0.2 pts", arrow: "down", tone: "good" },
    },
  ];
}

// ------------------------------------------------------------------ plans & accounts

export function planBreakdown(dayIdx = LAST): PlanRow[] {
  const t = dayIdx / (DAY_COUNT - 1);
  const { mrr, customers } = DAILY[dayIdx];
  return PLANS.map((p) => {
    const share = lerp(p.mrrShare[0], p.mrrShare[1], t);
    return {
      name: p.name,
      price: p.price,
      color: p.color,
      mrr: mrr * share,
      share: share * 100,
      customers: customers * lerp(p.customerShare[0], p.customerShare[1], t),
      churn: p.churn * (1.08 - 0.12 * t),
    };
  });
}

/** Twelve months of MRR for an account, ending at its current MRR. */
export function accountTrend(account: CustomerAccount, seed: number): number[] {
  const rng = createRng(seed + 1);
  const values = Array.from({ length: 12 }, (_, k) => {
    const t = k / 11;
    const shape =
      account.trend === "up"
        ? lerp(0.62, 1, t)
        : account.trend === "down"
          ? lerp(1.45, 1, t)
          : 1 + 0.02 * Math.sin(k);
    return account.mrr * shape * (1 + rng.uniform(-0.03, 0.03));
  });
  values[values.length - 1] = account.mrr;
  return values;
}

export const topAccounts = (count = CUSTOMERS.length) => CUSTOMERS.slice(0, count);
