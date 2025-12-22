/**
 * Deterministic daily revenue model for the sample workspace ("Quillstack", a fictional B2B SaaS company).
 * Every tile, chart, table and forecast in the demo is computed from these rows, so they always agree.
 */
import { addDays, differenceInCalendarDays } from "date-fns";

import { dayOfYear, isWeekday } from "@/lib/dates";
import { createRng, lerp } from "@/lib/random";
import type { DailyRevenue, Movement, MovementTotals } from "@/types/revenue";

export const FIRST_DAY = new Date(2024, 9, 1);
export const LAST_DAY = new Date(2026, 8, 24);
export const OPENING_MRR = 318_400;

export const WORKSPACE = {
  name: "Quillstack",
  currency: "USD",
  sources: "Stripe · Chargebee · HubSpot",
} as const;

/** Monthly MRR moved by each flow at the start and end of the model; interpolated in between. */
const MONTHLY_FLOW: Record<Movement, [number, number]> = {
  new: [14200, 21800],
  expansion: [11800, 17600],
  reactivation: [1250, 1900],
  contraction: [3400, 4300],
  churn: [6900, 7900],
};

const DAYS_PER_MONTH = 30.4;

function simulate(): DailyRevenue[] {
  const rng = createRng(20260924);
  const count = differenceInCalendarDays(LAST_DAY, FIRST_DAY) + 1;
  const rows: DailyRevenue[] = [];
  let mrr = OPENING_MRR;

  for (let i = 0; i < count; i++) {
    const date = addDays(FIRST_DAY, i);
    const t = i / (count - 1);
    const weekday = isWeekday(date) ? 1.18 : 0.55;
    const season = 1 + 0.08 * Math.sin((dayOfYear(date) / 365) * 2 * Math.PI + 1.2);

    const flows = {} as MovementTotals;
    for (const [key, [from, to]] of Object.entries(MONTHLY_FLOW) as Array<[Movement, [number, number]]>) {
      let v = (lerp(from, to, t) / DAYS_PER_MONTH) * (1 + rng.uniform(-0.45, 0.45));
      if (key === "new" || key === "expansion") v *= weekday * season; // sales close on weekdays
      if (key === "churn" && date.getDate() <= 3) v *= 2.1; // renewals cluster at month start
      flows[key] = v;
    }
    mrr += flows.new + flows.expansion + flows.reactivation - flows.contraction - flows.churn;

    const arpa = lerp(281, 318, t);
    const failed = ((mrr * 0.031) / DAYS_PER_MONTH) * (1 + rng.uniform(-0.3, 0.3));
    const recoveryRate = lerp(0.61, 0.71, t) + rng.uniform(-0.04, 0.04);

    rows.push({ date, flows, mrr, arpa, customers: mrr / arpa, failed, recovered: failed * recoveryRate });
  }
  return rows;
}

export const DAILY: readonly DailyRevenue[] = simulate();
export const DAY_COUNT = DAILY.length;
export const LAST = DAY_COUNT - 1;

export const dayIndex = (d: Date) => differenceInCalendarDays(d, FIRST_DAY);
