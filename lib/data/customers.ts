import type { CustomerAccount, CustomerStatus } from "@/types/revenue";

/** Largest and most-moved accounts in the sample workspace, highest MRR movement first. */
export const CUSTOMERS: CustomerAccount[] = [
  {
    name: "Harbor & Pine Studio",
    plan: "Scale",
    mrr: 2380,
    trend: "up",
    status: "Expanded",
    health: 92,
    since: "Mar 2023",
    owner: "Priya N.",
  },
  {
    name: "Tallgrass Labs",
    plan: "Enterprise",
    mrr: 6400,
    trend: "flat",
    status: "Active",
    health: 88,
    since: "Jan 2022",
    owner: "Marcus T.",
  },
  {
    name: "Copperleaf Health",
    plan: "Enterprise",
    mrr: 5120,
    trend: "up",
    status: "Expanded",
    health: 90,
    since: "Jun 2023",
    owner: "Priya N.",
  },
  {
    name: "Oakline Freight",
    plan: "Scale",
    mrr: 1190,
    trend: "down",
    status: "At risk",
    health: 41,
    since: "Aug 2024",
    owner: "Dana R.",
  },
  {
    name: "Brightfold Media",
    plan: "Growth",
    mrr: 698,
    trend: "up",
    status: "Active",
    health: 81,
    since: "Feb 2025",
    owner: "Dana R.",
  },
  {
    name: "Sparrow Legal",
    plan: "Growth",
    mrr: 349,
    trend: "flat",
    status: "Past due",
    health: 58,
    since: "Nov 2024",
    owner: "Marcus T.",
  },
  {
    name: "Meridian Dental Group",
    plan: "Scale",
    mrr: 1785,
    trend: "up",
    status: "Active",
    health: 84,
    since: "Sep 2023",
    owner: "Priya N.",
  },
  {
    name: "Kitewell Robotics",
    plan: "Growth",
    mrr: 1047,
    trend: "up",
    status: "Expanded",
    health: 87,
    since: "Apr 2025",
    owner: "Dana R.",
  },
  {
    name: "Lumen & Oak Co.",
    plan: "Starter",
    mrr: 99,
    trend: "down",
    status: "Downgraded",
    health: 52,
    since: "Jul 2025",
    owner: "Marcus T.",
  },
  {
    name: "Bluefin Payroll",
    plan: "Enterprise",
    mrr: 8900,
    trend: "flat",
    status: "Active",
    health: 95,
    since: "Oct 2021",
    owner: "Priya N.",
  },
  {
    name: "Quarry Street Supply",
    plan: "Growth",
    mrr: 349,
    trend: "down",
    status: "Churn scheduled",
    health: 22,
    since: "Dec 2024",
    owner: "Dana R.",
  },
  {
    name: "Fernhill Analytics",
    plan: "Scale",
    mrr: 2380,
    trend: "up",
    status: "Active",
    health: 79,
    since: "May 2024",
    owner: "Marcus T.",
  },
];

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

export interface ActivityItem {
  customer: string;
  detail: string;
  amount: string;
  direction: "p" | "m";
  glyph: string;
  color: string;
  when: string;
}

export const RECENT_ACTIVITY: ActivityItem[] = [
  {
    customer: "Harbor & Pine Studio",
    detail: "Upgraded Growth → Scale",
    amount: "+$841",
    direction: "p",
    glyph: "↗",
    color: "#0f7a56",
    when: "2h ago",
  },
  {
    customer: "Ridgeway Clinics",
    detail: "Payment recovered on retry 2",
    amount: "+$2,380",
    direction: "p",
    glyph: "↻",
    color: "#3cc28f",
    when: "4h ago",
  },
  {
    customer: "Quarry Street Supply",
    detail: "Scheduled cancellation · Budget cuts",
    amount: "−$349",
    direction: "m",
    glyph: "✕",
    color: "#d9463e",
    when: "6h ago",
  },
  {
    customer: "Kitewell Robotics",
    detail: "Added 12 seats",
    amount: "+$349",
    direction: "p",
    glyph: "+",
    color: "#0f7a56",
    when: "Yesterday",
  },
  {
    customer: "Lumen & Oak Co.",
    detail: "Downgraded Growth → Starter",
    amount: "−$250",
    direction: "m",
    glyph: "↘",
    color: "#eda100",
    when: "Yesterday",
  },
  {
    customer: "Northgate Tutors",
    detail: "New customer · Growth annual",
    amount: "+$698",
    direction: "p",
    glyph: "★",
    color: "#3a73d6",
    when: "Yesterday",
  },
];

/** Account timeline shown on the product page's customer profile. */
export const PROFILE = {
  name: "Harbor & Pine Studio",
  initials: "HP",
  plan: "Scale plan · customer since Mar 2023",
  status: "Expanded" as CustomerStatus,
  stats: [
    { label: "MRR", value: "$2,380" },
    { label: "Lifetime revenue", value: "$48.6k" },
    { label: "Health", value: "92 / 100" },
  ],
  timeline: [
    { date: "Sep 18", title: "Upgraded to Scale", detail: "Seats 18 → 30 · +$1,190 MRR", color: "#0f7a56" },
    {
      date: "Aug 02",
      title: "Payment recovered",
      detail: "Retry 2 succeeded after an expired card",
      color: "#3cc28f",
    },
    { date: "Jun 11", title: "Added Insights add-on", detail: "+$195 MRR", color: "#0f7a56" },
    {
      date: "Mar 04",
      title: "Downgrade scheduled, then cancelled",
      detail: "Saved by CS outreach",
      color: "#eda100",
    },
    { date: "Mar 14, 2023", title: "Started paying", detail: "Growth plan · annual", color: "#0d1f1a" },
  ],
};

export const CANCELLATION_REASONS: Array<[string, number]> = [
  ["Budget cuts", 26],
  ["Missing a feature", 19],
  ["Low usage", 17],
  ["Switched tools", 15],
  ["Company closed", 12],
  ["Other", 11],
];
