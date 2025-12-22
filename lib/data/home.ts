export const HERO_CONNECTORS = ["Stripe", "Chargebee", "Recurly", "Braintree", "Paddle"];

export const METRIC_STRIP = [
  {
    name: "Monthly recurring revenue",
    body: "Normalized from every plan, interval, discount and add-on. Annual plans spread over twelve months.",
    formula: "Σ active subscriptions / month",
  },
  {
    name: "Net revenue retention",
    body: "How much revenue last year's customers generate today, after expansion, contraction and churn.",
    formula: "(start + exp − contr − churn) / start",
  },
  {
    name: "Revenue & logo churn",
    body: "Split into voluntary cancellations and involuntary churn from failed payments, so you fix the right one.",
    formula: "churned MRR / starting MRR",
  },
  {
    name: "Lifetime value",
    body: "Margin-adjusted and segment-aware, recalculated nightly from real churn rather than a guess.",
    formula: "ARPA × margin / logo churn",
  },
];

/** Check-list items render the lead in bold. */
export type Check = { lead: string; rest: string };

export const FEATURE_CHECKS: Record<"movements" | "cohorts" | "forecast" | "recovery", Check[]> = {
  movements: [
    { lead: "Drill from any bar", rest: "to the list of customers that moved it." },
    { lead: "Segment by plan, region, channel", rest: "or any CRM field you sync in." },
    { lead: "Annotate launches and price changes", rest: "so the chart tells the story." },
  ],
  cohorts: [
    { lead: "Net and gross revenue retention", rest: "on the same grid." },
    { lead: "Filter cohorts by plan, acquisition channel", rest: "or sales-assisted vs self-serve." },
    { lead: "Export to CSV", rest: "or pin a cohort to your weekly email." },
  ],
  forecast: [
    { lead: "Conservative, base and stretch", rest: "scenarios for planning and hiring." },
    { lead: "80% confidence band", rest: "so nobody mistakes a guess for a promise." },
    { lead: "Share a read-only link", rest: "with your board or your investors." },
  ],
  recovery: [
    { lead: "Smart retries", rest: "tuned to each decline code." },
    { lead: "Email and in-app reminders", rest: "that sound like your team, not a collections agency." },
    { lead: "Recovered revenue tracked", rest: "right next to your churn numbers." },
  ],
};

export const ROLES = [
  {
    tag: "Founders",
    question: "Are we on track?",
    body: "A Monday email with MRR, net new and runway-relevant trends, plus a board-ready view you never have to rebuild.",
  },
  {
    tag: "Finance",
    question: "Does this tie out?",
    body: "Revenue numbers that reconcile to the billing system, with every adjustment logged and exportable.",
  },
  {
    tag: "Customer success",
    question: "Who's at risk?",
    body: "Downgrades, failed payments and usage drops flagged per account before renewal, not after.",
  },
  {
    tag: "Growth",
    question: "What's working?",
    body: "Compare trial conversion, ARPA and retention by channel, plan and pricing experiment.",
  },
];

export const TESTIMONIAL = {
  quote:
    "We used to spend the first week of every month rebuilding the same MRR spreadsheet. Now the numbers are just there, and we spend that week acting on them.",
  name: "Dana R.",
  role: "VP Finance at a B2B SaaS company",
};

export const INTEGRATIONS = [
  { name: "Stripe", kind: "Billing", mono: "S", color: "#4f5bd5" },
  { name: "Chargebee", kind: "Subscription billing", mono: "Cb", color: "#e5611f" },
  { name: "Recurly", kind: "Subscription billing", mono: "Rc", color: "#6b4fbb" },
  { name: "Braintree", kind: "Payments", mono: "Bt", color: "#1f2b3a" },
  { name: "Paddle", kind: "Merchant of record", mono: "Pd", color: "#2a8c6a" },
  { name: "App Store & Google Play", kind: "In-app subscriptions", mono: "Ap", color: "#3a73d6" },
  { name: "HubSpot & Salesforce", kind: "CRM enrichment", mono: "Cr", color: "#c2362f" },
  { name: "Custom source (API / CSV)", kind: "Anything else", mono: "{}", color: "#0d1f1a" },
];
