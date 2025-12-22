import { TRIAL_URL } from "./site";

export interface Plan {
  name: string;
  audience: string;
  price: string;
  cap: string;
  popular?: boolean;
  /** First entry is the group heading ("Everything in Starter, plus"). */
  features: [heading: string, ...items: string[]];
}

export const PLANS: Plan[] = [
  {
    name: "Starter",
    audience: "For early SaaS teams getting their first clean MRR number.",
    price: "$79",
    cap: "Up to $25k MRR",
    features: [
      "Includes",
      "Core metrics: MRR, churn, ARPA, LTV",
      "One billing connection",
      "Customer profiles",
      "Weekly email digest",
      "Email support",
    ],
  },
  {
    name: "Growth",
    audience: "For teams that review revenue every week and want to act on it.",
    price: "$249",
    cap: "Up to $150k MRR",
    popular: true,
    features: [
      "Everything in Starter, plus",
      "Cohorts & retention",
      "Unlimited segments",
      "CRM enrichment",
      "Three billing connections",
      "Slack alerts & goals",
    ],
  },
  {
    name: "Scale",
    audience: "For finance and RevOps teams planning the next 12 months.",
    price: "$690",
    cap: "Up to $750k MRR",
    features: [
      "Everything in Growth, plus",
      "Forecasting & scenarios",
      "API & warehouse sync",
      "Unlimited connections",
      "SSO & role-based access",
      "Priority support",
    ],
  },
  {
    name: "Enterprise",
    audience: "For larger companies with custom billing, contracts and security review.",
    price: "Custom",
    cap: "$750k+ MRR",
    features: [
      "Everything in Scale, plus",
      "Custom metric definitions",
      "Invoiced & offline revenue",
      "Security review & DPA",
      "Dedicated success manager",
      "Onboarding & data migration",
    ],
  },
];

export const planCta = (plan: Plan) => ({
  href: TRIAL_URL,
  label: plan.price === "Custom" ? "Contact sales" : "Start free trial",
});

export const ADD_ONS = [
  {
    name: "Payment recovery",
    summary: "Smart retries, reminder emails, in-app banners and a hosted card-update page.",
    price: "+$149",
    points: [
      "Retry timing tuned to each decline code",
      "Branded email sequences and card-update page",
      "Recovered revenue reported next to churn",
    ],
  },
  {
    name: "Cancellation insights",
    summary: "Ask why customers cancel, tie every answer to lost MRR and follow up automatically.",
    price: "+$99",
    points: [
      "Customizable in-app cancellation survey",
      "Lost MRR by reason, plan and segment",
      "Win-back emails and pause-instead offers",
    ],
  },
];

/** `true` renders a check, `false` a dash. Columns: Starter, Growth, Scale, Enterprise. */
export type Cell = string | boolean;

export const COMPARISON: Array<{
  group: string;
  rows: Array<[feature: string, cells: [Cell, Cell, Cell, Cell]]>;
}> = [
  {
    group: "Analytics",
    rows: [
      ["MRR, ARR, churn, ARPA, LTV", [true, true, true, true]],
      ["MRR movements & customer drill-down", [true, true, true, true]],
      ["Cohorts & net revenue retention", [false, true, true, true]],
      ["Segments", ["3", "Unlimited", "Unlimited", "Unlimited"]],
      ["Forecasting & scenarios", [false, false, true, true]],
    ],
  },
  {
    group: "Data",
    rows: [
      ["Billing connections", ["1", "3", "Unlimited", "Unlimited"]],
      ["CRM enrichment", [false, true, true, true]],
      ["API & warehouse sync", [false, false, true, true]],
      ["Custom metric definitions", [false, false, false, true]],
    ],
  },
  {
    group: "Team & security",
    rows: [
      ["Seats", ["3", "10", "Unlimited", "Unlimited"]],
      ["SSO & role-based access", [false, false, true, true]],
      ["Support", ["Email", "Email & chat", "Priority", "Dedicated manager"]],
    ],
  },
];

export const PRICING_FAQ = [
  {
    q: "How is my plan tier decided?",
    a: "By the MRR Churnwise tracks for you, averaged over the last three months. If you grow past a tier, we'll let you know a month before anything changes.",
  },
  {
    q: "Do you import my historical data?",
    a: "Yes. On every plan, Churnwise backfills your complete billing history when you connect, so your charts start from your first paying customer.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Monthly plans can be cancelled at any time and stay active until the end of the billing period. You can export all your metrics and customer data as CSV before you go.",
  },
  {
    q: "Is there a discount for early-stage startups?",
    a: "Startups under $10k MRR get Growth features at the Starter price for their first year. Email us with a link to your product.",
  },
  {
    q: "What does read-only access mean?",
    a: "Churnwise asks your billing system for read-only keys for analytics. Payment recovery needs limited write access to retry charges and save updated cards, and you can enable it separately.",
  },
];
