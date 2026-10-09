/**
 * Shapes returned by the Churnwise engine (`engine/`). The web app never computes revenue metrics itself;
 * it renders what `GET /api/dashboard` returns. Dates arrive as ISO strings.
 */

/** The five ways MRR can change. Every metric in the product is derived from these flows. */
export type Movement = "new" | "expansion" | "reactivation" | "contraction" | "churn";
export type MovementTotals = Record<Movement, number>;

export type RangeKey = "30d" | "90d" | "12m" | "24m";
export type TabKey = "overview" | "revenue" | "retention" | "customers" | "forecast" | "recovery";
export type Scenario = "conservative" | "base" | "stretch";
export type CohortMetric = "net" | "logo";

/** Semantic colour roles; `lib/palette.ts` maps them to colours. */
export type Tone = "brand" | "brand_dark" | "ink" | "mint" | "blue" | "amber" | "red" | "starter";

export interface Workspace {
  name: string;
  slug: string;
  currency: string;
  sources: string;
  asOf: string;
  asOfLabel: string;
}

export interface RangeDefinition {
  key: RangeKey;
  label: string;
  short: string;
  bucket: "day" | "week" | "month";
  comparisonNote: string;
}

export interface MovementBucket extends MovementTotals {
  label: string;
  /** Day indices [start, end) into the daily series. */
  start: number;
  end: number;
  net: number;
  endingMrr: number;
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
  sparkTone?: Tone;
}

export interface ChartPoint {
  label: string;
  value: number;
  tip?: string;
}

export interface RangeView {
  range: RangeKey;
  stats: RangeStats;
  /** Headline MRR line, already labelled for the range. */
  line: ChartPoint[];
  labelEvery: number;
  buckets: MovementBucket[];
  totals: MovementTotals;
  gained: number;
  lost: number;
  quickRatio: number;
  kpis: Kpi[];
}

export interface Cohort {
  month: string;
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
  tone: Tone;
  mrr: number;
  share: number;
  customers: number;
  churn: number;
}

export type CustomerStatus =
  "Expanded" | "Active" | "At risk" | "Past due" | "Downgraded" | "Churn scheduled";

export interface CustomerAccount {
  name: string;
  plan: string;
  mrr: number;
  trend: "up" | "flat" | "down";
  status: CustomerStatus;
  health: number;
  since: string;
  owner: string;
  /** Twelve months of MRR, ending at the current MRR. */
  history: number[];
}

export type ActivityKind = "upgrade" | "recovered" | "cancellation" | "seats" | "downgrade" | "new";

export interface ActivityItem {
  customer: string;
  detail: string;
  kind: ActivityKind;
  amount: number;
  amountLabel: string;
  when: string;
}

export interface RetentionView {
  kpis: Kpi[];
  series: { labels: string[]; nrr: number[]; grr: number[] };
  cohorts: Cohort[];
  averages: Record<CohortMetric, Array<number | null>>;
  cancellationReasons: Array<[string, number]>;
}

export interface CustomersView {
  kpis: Kpi[];
  total: number;
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

export interface ForecastRow {
  month: string;
  low: number;
  projected: number;
  high: number;
  netNew: number;
  runRateArr: number;
}

export interface ScenarioView {
  key: Scenario;
  label: string;
  multiplier: number;
  assumptions: { newBusiness: string; expansion: string; cancelled: string; reactivation: string };
  forecast: Forecast;
  table: ForecastRow[];
  end: number;
  monthsToTarget: number | null;
}

export interface ForecastView {
  scenarios: ScenarioView[];
  currentMrr: number;
  horizonMonths: number;
  horizonLabel: string;
  horizonShortLabel: string;
  target: number;
}

export interface FunnelItem {
  key: string;
  label: string;
  value: number;
  tone: Tone;
}

export interface MonthlyRecovery {
  label: string;
  failed: number;
  recovered: number;
}

export interface OpenFailedPayment {
  customer: string;
  amount: number;
  reason: string;
  declineCode: string;
  attempts: number;
  nextRetry: string;
  step: string;
}

export interface RecoveryView {
  kpis: Kpi[];
  funnel: { items: FunnelItem[]; failed: number; recovered: number; rate: number };
  months: MonthlyRecovery[];
  declineReasons: Array<[string, number]>;
  openFailed: OpenFailedPayment[];
  maxAttempts: number;
}

export interface CustomerProfile {
  name: string;
  initials: string;
  plan: string;
  status: CustomerStatus;
  stats: Array<{ label: string; value: string }>;
  timeline: Array<{ date: string; title: string; detail: string; tone: Tone }>;
}

/** `GET /api/dashboard`: every tab, range and scenario of the sample workspace. */
export interface DashboardSnapshot {
  workspace: Workspace;
  ranges: RangeDefinition[];
  views: Record<RangeKey, RangeView>;
  plans: PlanRow[];
  accounts: CustomerAccount[];
  activity: ActivityItem[];
  retention: RetentionView;
  customers: CustomersView;
  forecast: ForecastView;
  recovery: RecoveryView;
  profile: CustomerProfile;
}
