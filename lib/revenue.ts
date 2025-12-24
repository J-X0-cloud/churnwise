/**
 * Revenue math: MRR movements, net/gross revenue retention, churn rates, cohort averages and the
 * rules that turn a billing event into an MRR movement. Everything here works on the daily model or
 * on plain numbers, so the same functions serve the dashboards, the API and the webhook pipeline.
 */
import { addMonths } from "date-fns";

import { dayLabel, monthLabel, startOfMonth } from "@/lib/dates";
import { DAILY, DAY_COUNT, FIRST_DAY, LAST, LAST_DAY, dayIndex } from "@/lib/data/simulation";
import type {
  Cohort,
  CohortMetric,
  Movement,
  MovementBucket,
  MovementTotals,
  RangeDefinition,
  RangeKey,
  RangeStats,
} from "@/types/revenue";

export const MOVEMENT_KEYS: Movement[] = ["new", "expansion", "reactivation", "contraction", "churn"];

/** Assumed gross margin used in LTV. */
export const GROSS_MARGIN = 0.82;
/** Logo churn runs ahead of revenue churn because small accounts churn more often. */
const LOGO_TO_REVENUE_CHURN = 1.22;
const DAYS_PER_MONTH = 30.4;

// ------------------------------------------------------------------ flows

export function sumFlow(key: Movement, from: number, to: number): number {
  let total = 0;
  for (let i = Math.max(0, from); i < Math.min(to, DAY_COUNT); i++) total += DAILY[i].flows[key];
  return total;
}

export function flowTotals(from: number, to: number): MovementTotals {
  return Object.fromEntries(MOVEMENT_KEYS.map((k) => [k, sumFlow(k, from, to)])) as MovementTotals;
}

export const gained = (t: MovementTotals) => t.new + t.expansion + t.reactivation;
export const lost = (t: MovementTotals) => t.contraction + t.churn;
export const netNew = (t: MovementTotals) => gained(t) - lost(t);

/** Gained MRR for every dollar lost. Above 4 is efficient growth. */
export const quickRatio = (t: MovementTotals) => gained(t) / lost(t);

export function sumTotals(buckets: MovementTotals[]): MovementTotals {
  return Object.fromEntries(
    MOVEMENT_KEYS.map((k) => [k, buckets.reduce((s, b) => s + b[k], 0)]),
  ) as MovementTotals;
}

// ------------------------------------------------------------------ retention

/**
 * Trailing-12-month net revenue retention at day `i`: what last year's customers pay today as a share of
 * what they paid then. Part of the window's expansion comes from customers acquired inside it, so the
 * movement is scaled to the base cohort.
 */
export function nrrAt(i: number): number {
  const j = Math.max(0, i - 365);
  const base = DAILY[j].mrr;
  const change =
    sumFlow("expansion", j, i) +
    sumFlow("reactivation", j, i) -
    sumFlow("contraction", j, i) -
    sumFlow("churn", j, i);
  return (100 * (base + change * 0.74)) / base;
}

/** Gross revenue retention ignores expansion, so it can never exceed 100%. */
export function grrAt(i: number): number {
  const j = Math.max(0, i - 365);
  return (
    (100 * (DAILY[j].mrr - (sumFlow("contraction", j, i) + sumFlow("churn", j, i)) * 0.42)) / DAILY[j].mrr
  );
}

/** Churned + contracted MRR over the trailing 30 days as a share of MRR on day `i`. */
export function trailingChurnRate(i: number): number {
  return ((sumFlow("churn", i - 30, i + 1) + sumFlow("contraction", i - 30, i + 1)) / DAILY[i].mrr) * 100;
}

export function cohortAverage(
  cohorts: readonly Cohort[],
  metric: CohortMetric,
  months: number,
): Array<number | null> {
  return Array.from({ length: months }, (_, k) => {
    const values = cohorts.filter((c) => k < c[metric].length).map((c) => c[metric][k]);
    return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
  });
}

// ------------------------------------------------------------------ calendar

export interface MonthWindow {
  start: Date;
  /** Day indices [from, to) into the daily series. */
  from: number;
  to: number;
}

export const MONTHS: MonthWindow[] = (() => {
  const out: MonthWindow[] = [];
  for (let d = FIRST_DAY; d <= LAST_DAY; d = addMonths(d, 1)) {
    const next = addMonths(d, 1);
    out.push({ start: d, from: dayIndex(d), to: Math.min(dayIndex(next), DAY_COUNT) });
  }
  return out;
})();

/** MRR on the last day of a month window. */
export const monthEndMrr = (m: MonthWindow) => DAILY[m.to - 1].mrr;

// ------------------------------------------------------------------ ranges

export const RANGES: Record<RangeKey, RangeDefinition> = {
  "30d": { key: "30d", label: "Last 30 days", short: "30D", bucket: "day", comparisonNote: "vs 30 days ago" },
  "90d": {
    key: "90d",
    label: "Last 90 days",
    short: "90D",
    bucket: "week",
    comparisonNote: "vs 90 days ago",
  },
  "12m": {
    key: "12m",
    label: "Last 12 months",
    short: "12M",
    bucket: "month",
    comparisonNote: "vs Oct 1, 2025",
  },
  "24m": {
    key: "24m",
    label: "Last 24 months",
    short: "24M",
    bucket: "month",
    comparisonNote: "vs Oct 1, 2024",
  },
};

export const RANGE_KEYS = Object.keys(RANGES) as RangeKey[];

export function rangeStart(range: RangeKey): number {
  switch (range) {
    case "30d":
      return DAY_COUNT - 30;
    case "90d":
      return DAY_COUNT - 91;
    case "12m":
      return dayIndex(startOfMonth(addMonths(LAST_DAY, -11)));
    case "24m":
      return 0;
  }
}

/** Movement totals per chart bucket: days for 30D, weeks for 90D, calendar months otherwise. */
export function movementBuckets(range: RangeKey): MovementBucket[] {
  const start = rangeStart(range);
  const windows: Array<{ label: string; from: number; to: number }> = [];

  if (RANGES[range].bucket === "day") {
    for (let i = start; i < DAY_COUNT; i++)
      windows.push({ label: dayLabel(DAILY[i].date), from: i, to: i + 1 });
  } else if (RANGES[range].bucket === "week") {
    for (let i = start; i < DAY_COUNT; i += 7)
      windows.push({ label: dayLabel(DAILY[i].date), from: i, to: Math.min(i + 7, DAY_COUNT) });
  } else {
    for (const m of MONTHS.filter((w) => w.from >= start)) {
      const withYear = m.start.getMonth() === 0 || (range === "24m" && m.from === 0);
      windows.push({ label: monthLabel(m.start, withYear), from: m.from, to: m.to });
    }
  }

  return windows.map((w) => {
    const totals = flowTotals(w.from, w.to);
    return { label: w.label, start: w.from, end: w.to, ...totals, net: netNew(totals) };
  });
}

/** Headline numbers for a range, each paired with its value at the start of the range or in the prior period. */
export function rangeStats(range: RangeKey): RangeStats {
  const s = rangeStart(range);
  const length = DAY_COUNT - s;
  const ps = s - length;
  const hasPrior = ps >= 0;
  const perMonth = DAYS_PER_MONTH / length;

  const avgMrr = (from: number, to: number) =>
    DAILY.slice(from, to).reduce((a, r) => a + r.mrr, 0) / (to - from);
  const churnRate =
    ((sumFlow("churn", s, DAY_COUNT) + sumFlow("contraction", s, DAY_COUNT)) / avgMrr(s, DAY_COUNT)) *
    perMonth *
    100;
  const churnRatePrior = hasPrior
    ? ((sumFlow("churn", ps, s) + sumFlow("contraction", ps, s)) / avgMrr(ps, s)) * perMonth * 100
    : null;

  const logoChurn = (churnRate * LOGO_TO_REVENUE_CHURN) / 100;
  const logoChurnPrior = ((churnRatePrior ?? churnRate * 1.06) * LOGO_TO_REVENUE_CHURN) / 100;
  const sumRange = (key: "failed" | "recovered", from: number, to: number) =>
    DAILY.slice(from, to).reduce((a, r) => a + r[key], 0);

  const step = RANGES[range].bucket === "month" ? 7 : 1;
  const line: RangeStats["line"] = [];
  for (let i = s; i < DAY_COUNT; i += step) line.push({ date: DAILY[i].date, value: DAILY[i].mrr });
  if (line[line.length - 1].date !== DAILY[LAST].date)
    line.push({ date: DAILY[LAST].date, value: DAILY[LAST].mrr });

  return {
    range,
    label: RANGES[range].label,
    start: s,
    mrr: DAILY[LAST].mrr,
    mrrStart: DAILY[s].mrr,
    netNew: DAILY[LAST].mrr - DAILY[s].mrr,
    netNewPrior: hasPrior ? DAILY[s].mrr - DAILY[ps].mrr : null,
    churnRate,
    churnRatePrior,
    nrr: nrrAt(LAST),
    nrrStart: nrrAt(Math.max(s, 365)),
    customers: DAILY[LAST].customers,
    customersStart: DAILY[s].customers,
    arpa: DAILY[LAST].arpa,
    arpaStart: DAILY[s].arpa,
    ltv: (DAILY[LAST].arpa * GROSS_MARGIN) / logoChurn,
    ltvStart: (DAILY[s].arpa * GROSS_MARGIN) / logoChurnPrior,
    recovered: sumRange("recovered", s, DAY_COUNT),
    recoveredPrior: hasPrior ? sumRange("recovered", ps, s) : null,
    recoveryRate: (sumRange("recovered", s, DAY_COUNT) / sumRange("failed", s, DAY_COUNT)) * 100,
    failed: sumRange("failed", s, DAY_COUNT),
    line,
  };
}

// ------------------------------------------------------------------ billing events → movements

export type BillingInterval = "day" | "week" | "month" | "year";

/** Normalise a recurring price to a monthly amount (annual plans spread over twelve months). */
export function monthlyValue(
  unitAmount: number,
  quantity: number,
  interval: BillingInterval,
  intervalCount = 1,
): number {
  const perInterval = unitAmount * quantity;
  const months =
    { day: 1 / DAYS_PER_MONTH, week: 7 / DAYS_PER_MONTH, month: 1, year: 12 }[interval] * intervalCount;
  return perInterval / months;
}

export interface SubscriptionState {
  mrr: number;
  /** Whether the customer had ever paid before this subscription started. */
  previouslyChurned: boolean;
}

/**
 * Classify a change in a customer's MRR. Returns null when MRR is unchanged (e.g. a renewal or a
 * payment method update), which is why most billing events never become movements.
 */
export function classifyMovement(
  before: SubscriptionState | null,
  afterMrr: number,
): { movement: Movement; amount: number } | null {
  const prev = before?.mrr ?? 0;
  const delta = afterMrr - prev;
  if (Math.abs(delta) < 0.005) return null;
  if (prev === 0) return { movement: before?.previouslyChurned ? "reactivation" : "new", amount: afterMrr };
  if (afterMrr === 0) return { movement: "churn", amount: prev };
  return delta > 0 ? { movement: "expansion", amount: delta } : { movement: "contraction", amount: -delta };
}
