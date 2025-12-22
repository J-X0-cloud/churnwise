/** The five ways MRR can change. Every metric in the product is derived from these flows. */
export type Movement = "new" | "expansion" | "reactivation" | "contraction" | "churn";
export type MovementTotals = Record<Movement, number>;

export type RangeKey = "30d" | "90d" | "12m" | "24m";
export type TabKey = "overview" | "revenue" | "retention" | "customers" | "forecast" | "recovery";
export type Scenario = "conservative" | "base" | "stretch";
export type CohortMetric = "net" | "logo";

/** One day of the workspace's revenue model. `flows` are MRR amounts moved that day. */
export interface DailyRevenue {
  date: Date;
  flows: MovementTotals;
  /** MRR at end of day. */
  mrr: number;
  arpa: number;
  customers: number;
  /** Value of charges that failed that day, and how much of it was eventually recovered. */
  failed: number;
  recovered: number;
}

export interface MovementBucket extends MovementTotals {
  label: string;
  /** Day indices [start, end) into the daily series. */
  start: number;
  end: number;
  net: number;
}

export interface RangeDefinition {
  key: RangeKey;
  label: string;
  short: string;
  bucket: "day" | "week" | "month";
  comparisonNote: string;
}

export interface RangeStats {
  range: RangeKey;
  label: string;
  start: number;
  mrr: number;
  mrrStart: number;
  netNew: number;
  netNewPrior: number | null;
  churnRate: number;
  churnRatePrior: number | null;
  nrr: number;
  nrrStart: number;
  customers: number;
  customersStart: number;
  arpa: number;
  arpaStart: number;
  ltv: number;
  ltvStart: number;
  recovered: number;
  recoveredPrior: number | null;
  recoveryRate: number;
  failed: number;
  /** MRR sampled for the headline line chart. */
  line: Array<{ date: Date; value: number }>;
}

export interface Delta {
  text: string;
  tone: "good" | "bad" | "neutral";
  arrow?: "up" | "down";
}

export interface Kpi {
  label: string;
  value: string;
  /** Rendered small after the value, e.g. "/mo". */
  unit?: string;
  hint?: string;
  delta: Delta;
  spark?: number[];
  sparkColor?: string;
}

export interface Cohort {
  month: Date;
  label: string;
  customers: number;
  startMrr: number;
  /** % of starting MRR (net) or of starting customers (logo) retained, by months since signup. */
  net: number[];
  logo: number[];
}

export interface PlanRow {
  name: string;
  price: string;
  color: string;
  mrr: number;
  share: number;
  customers: number;
  churn: number;
}

export type CustomerStatus =
  | "Expanded"
  | "Active"
  | "At risk"
  | "Past due"
  | "Downgraded"
  | "Churn scheduled";

export interface CustomerAccount {
  name: string;
  plan: string;
  mrr: number;
  trend: "up" | "flat" | "down";
  status: CustomerStatus;
  health: number;
  since: string;
  owner: string;
}

export interface ForecastPoint {
  label: string;
  value: number;
}

export interface Forecast {
  scenario: Scenario;
  history: ForecastPoint[];
  projection: ForecastPoint[];
  /** 80% interval per projected month. */
  band: Array<[number, number]>;
}

export interface MonthlyRecovery {
  label: string;
  failed: number;
  recovered: number;
}

export interface FunnelItem {
  label: string;
  value: number;
  color: string;
}
