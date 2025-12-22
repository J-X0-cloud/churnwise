export const CONTACT_EMAIL = "hello@churnwise.com";
/** Trials and sales conversations both start with an email to the team. */
export const TRIAL_URL = `mailto:${CONTACT_EMAIL}`;

export const NAV_LINKS = [
  { href: "/product", label: "Product" },
  { href: "/recovery", label: "Recovery" },
  { href: "/pricing", label: "Pricing" },
  { href: "/demo", label: "Live demo" },
] as const;

export const FOOTER_COLUMNS = [
  {
    title: "Product",
    links: [
      { href: "/product", label: "Revenue analytics" },
      { href: "/product#cohorts", label: "Cohorts & retention" },
      { href: "/product#forecast", label: "Forecasting" },
      { href: "/recovery", label: "Payment recovery" },
      { href: "/demo", label: "Live demo" },
    ],
  },
  {
    title: "Resources",
    links: [
      { href: "/product#metrics", label: "Metric definitions" },
      { href: "#", label: "API reference" },
      { href: "#", label: "Help center" },
      { href: "#", label: "Changelog" },
    ],
  },
  {
    title: "Company",
    links: [
      { href: "/pricing", label: "Pricing" },
      { href: "#", label: "Security" },
      { href: TRIAL_URL, label: "Contact sales" },
      { href: "#", label: "Careers" },
    ],
  },
];

export const TAGLINE =
  "Subscription revenue analytics for SaaS teams. MRR, retention, cohorts, forecasts and failed-payment recovery from the billing data you already have.";

export const DEFAULT_CTA = {
  title: "See your own revenue in Churnwise by this afternoon.",
  body: "Connect your billing system read-only, and your full history of MRR, churn and cohorts is ready in minutes. Free for 14 days, no card required.",
};
