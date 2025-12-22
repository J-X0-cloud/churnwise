import type { Check } from "./home";

export const DECLINE_REASONS: Array<[string, number]> = [
  ["Insufficient funds", 34],
  ["Expired card", 22],
  ["Generic decline", 17],
  ["Do not honor", 11],
  ["Card reported lost", 6],
  ["Authentication required", 6],
  ["Processing error", 4],
];

export interface OpenFailedPayment {
  customer: string;
  amount: number;
  reason: string;
  attempts: number;
  nextRetry: string;
  step: string;
}

export { MAX_ATTEMPTS } from "@/lib/billing/retry-policy";

export const OPEN_FAILED: OpenFailedPayment[] = [
  {
    customer: "Sparrow Legal",
    amount: 349,
    reason: "Insufficient funds",
    attempts: 2,
    nextRetry: "Sep 27",
    step: "Email 2 sent",
  },
  {
    customer: "Northgate Tutors",
    amount: 698,
    reason: "Expired card",
    attempts: 1,
    nextRetry: "Sep 25",
    step: "Card update link sent",
  },
  {
    customer: "Pebble & Loom",
    amount: 99,
    reason: "Do not honor",
    attempts: 3,
    nextRetry: "Sep 28",
    step: "In-app banner live",
  },
  {
    customer: "Varsity Ops",
    amount: 1190,
    reason: "Authentication required",
    attempts: 1,
    nextRetry: "Sep 25",
    step: "3DS link sent",
  },
  {
    customer: "Ridgeway Clinics",
    amount: 2380,
    reason: "Insufficient funds",
    attempts: 1,
    nextRetry: "Sep 26",
    step: "Smart retry scheduled",
  },
  {
    customer: "Cobalt Kitchen Co.",
    amount: 349,
    reason: "Generic decline",
    attempts: 4,
    nextRetry: "Sep 30",
    step: "Final notice queued",
  },
];

export const RETRY_TIMELINE = [
  {
    day: "Day 0",
    title: "Charge declined",
    body: "Decline code read and classified. Customer keeps access.",
  },
  { day: "Day 1", title: "Retry #1", body: "Scheduled for the hour this card's bank approves most." },
  { day: "Day 3", title: "Reminder email", body: "Friendly note with a one-click card-update link." },
  { day: "Day 6", title: "In-app banner", body: "Shown to admins only, with the same update link." },
  {
    day: "Day 7",
    title: "Recovered",
    body: "Retry #3 succeeds. Your team is notified and the MRR is kept.",
    win: true,
  },
];

export const REMINDER_SEQUENCE = [
  {
    day: "Day 1",
    subject: "Quick heads-up about your payment",
    preview: "We couldn't process your card ending in 4242. No action needed yet, we'll try again tomorrow.",
    state: "Sent",
  },
  {
    day: "Day 3",
    subject: "Update your card in 10 seconds",
    preview: "One click, no login, and your workspace stays exactly as it is.",
    state: "Opened",
  },
  {
    day: "Day 7",
    subject: "Your account needs attention",
    preview: "Your account owner is copied. Reply to this email if something's changed.",
    state: "Queued",
  },
  {
    day: "Day 14",
    subject: "Final notice before your plan pauses",
    preview: "We'll hold your data for 60 days so you can pick up where you left off.",
    state: "Queued",
  },
];

export const RECOVERY_FAQ = [
  {
    q: "Does recovery replace my billing system's own retries?",
    a: "You choose. Most teams turn off the default retry schedule and let Churnwise handle timing, since it adjusts per decline code. If you'd rather keep your existing retries, Churnwise can run the emails and card-update page only.",
  },
  {
    q: "Can customers update their card without logging in?",
    a: "Yes. Each reminder carries a secure, single-use link to a hosted page in your branding. The new card is saved straight to your billing system; Churnwise never stores card numbers.",
  },
  {
    q: "How is recovered revenue counted?",
    a: "A payment counts as recovered when it succeeds after a failure within the recovery window you set (30 days by default). It's reported separately, so you can compare it with involuntary churn on the same dashboard.",
  },
  {
    q: "Which billing systems are supported?",
    a: "Recovery works with Stripe, Chargebee, Recurly and Braintree. Analytics covers those plus Paddle, app-store subscriptions and custom sources.",
  },
];

export const RECOVERY_CHECKS: Check[] = [
  { lead: "Different sequences", rest: "for monthly, annual and high-value accounts." },
  { lead: "Copy your CS owner", rest: "on the final notice for big customers." },
  { lead: "Pause access or keep it on", rest: ", your call per plan." },
];
