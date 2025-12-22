import type { IconName } from "@/components/ui/icons";

import type { Check } from "./home";

export const CAPABILITY_CARDS: Array<{ icon: IconName; title: string; body: string }> = [
  {
    icon: "events",
    title: "Rebuilt from raw events",
    body: "Invoices, subscription changes, credits and refunds are replayed in order, so mid-cycle upgrades, prorations and paused plans are counted correctly.",
  },
  {
    icon: "merge",
    title: "Multiple billing sources, one customer",
    body: "Merge web billing, app-store subscriptions and invoiced enterprise deals into one record per customer and one MRR number.",
  },
  {
    icon: "segments",
    title: "Segments on any field",
    body: "Filter by plan, country, billing interval, acquisition channel or any property synced from your CRM, and save views for your team.",
  },
];

export const PLATFORM_CARDS: Array<{ icon: IconName; title: string; body: string }> = [
  {
    icon: "report",
    title: "Scheduled reports",
    body: "A weekly or monthly email digest for founders and the board, and a Slack message whenever MRR crosses a goal.",
  },
  {
    icon: "api",
    title: "API & warehouse sync",
    body: "Pull any metric by REST API, or sync daily tables to your data warehouse for your own modeling.",
  },
  {
    icon: "shield",
    title: "Security by default",
    body: "Read-only billing keys, encryption in transit and at rest, SSO and role-based access for finance-only views.",
  },
];

/** Trailing-12-month NRR by segment; the chart axis runs 80–120%. */
export const SEGMENT_NRR: Array<{ segment: string; nrr: number }> = [
  { segment: "Self-serve", nrr: 94.2 },
  { segment: "Sales-assisted", nrr: 112.8 },
  { segment: "Partner referral", nrr: 106.1 },
  { segment: "Annual plans", nrr: 109.4 },
  { segment: "Monthly plans", nrr: 97.6 },
];

export const SEGMENT_CHECKS: Check[] = [
  { lead: "Saved segments", rest: "shared across dashboards, reports and alerts." },
  { lead: "CRM enrichment", rest: "for industry, company size and owner." },
];

export const PROFILE_CHECKS: Check[] = [
  { lead: "Health score", rest: "built from payment history, seat trends and plan changes." },
  { lead: "Alerts to your CS channel", rest: "when a big account downgrades or a card fails." },
];

export const METRIC_DEFINITIONS = [
  {
    metric: "MRR",
    meaning:
      "Normalized monthly value of all active, paid subscriptions. Annual and quarterly plans are divided by their length; one-off charges and taxes are excluded.",
    formula: "Σ normalized plan value",
  },
  {
    metric: "Net new MRR",
    meaning: "The change in MRR over a period, broken into its five movements.",
    formula: "new + expansion + reactivation − contraction − churn",
  },
  {
    metric: "Net revenue retention",
    meaning: "Revenue today from customers who were paying 12 months ago, as a share of what they paid then.",
    formula: "(MRR₀ + exp − contr − churn) / MRR₀",
  },
  {
    metric: "Gross revenue retention",
    meaning: "Like NRR, but expansion isn't counted, so it can never exceed 100%.",
    formula: "(MRR₀ − contr − churn) / MRR₀",
  },
  {
    metric: "Revenue churn rate",
    meaning: "Churned and contracted MRR as a share of MRR at the start of the month.",
    formula: "(churn + contraction) / MRR₀",
  },
  {
    metric: "Logo churn rate",
    meaning: "Share of paying customers who cancelled during the month.",
    formula: "cancelled customers / customers₀",
  },
  { metric: "ARPA", meaning: "Average revenue per paying account.", formula: "MRR / paying customers" },
  {
    metric: "LTV",
    meaning: "Expected gross-margin value of a customer over their lifetime.",
    formula: "ARPA × gross margin / logo churn",
  },
  {
    metric: "Quick ratio",
    meaning: "How efficiently you grow: gained MRR for every dollar lost.",
    formula: "(new + exp + react) / (contr + churn)",
  },
];
