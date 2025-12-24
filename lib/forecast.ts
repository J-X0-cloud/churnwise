/**
 * MRR forecast: projects the trailing-quarter net-new pace forward twelve months under three scenarios,
 * with an 80% interval that widens with the horizon.
 */
import { addMonths } from "date-fns";

import { monthLabel } from "@/lib/dates";
import { AMBER, BLUE, BRAND } from "@/lib/palette";
import { MONTHS, monthEndMrr } from "@/lib/revenue";
import { DAILY, LAST } from "@/lib/data/simulation";
import type { Forecast, Scenario } from "@/types/revenue";

export const SCENARIOS: Array<{ key: Scenario; label: string; multiplier: number; color: string }> = [
  { key: "conservative", label: "Conservative", multiplier: 0.62, color: AMBER },
  { key: "base", label: "Base", multiplier: 1, color: BRAND },
  { key: "stretch", label: "Stretch", multiplier: 1.32, color: BLUE },
];

export const scenarioMeta = (key: Scenario) => SCENARIOS.find((s) => s.key === key)!;

/** Monthly assumptions shown next to each scenario. */
export const SCENARIO_ASSUMPTIONS: Record<
  Scenario,
  { newBusiness: string; expansion: string; cancelled: string; reactivation: string }
> = {
  conservative: { newBusiness: "$15.1k", expansion: "1.9%", cancelled: "1.4%", reactivation: "0.3%" },
  base: { newBusiness: "$18.9k", expansion: "2.3%", cancelled: "1.3%", reactivation: "0.3%" },
  stretch: { newBusiness: "$22.4k", expansion: "2.7%", cancelled: "1.1%", reactivation: "0.3%" },
};

const HORIZON = 12;
/** Net-new pace compounds slightly as the customer base grows. */
const PACE_GROWTH = 0.012;

export function forecast(scenario: Scenario): Forecast {
  const history = MONTHS.slice(-12).map((m) => ({
    label: monthLabel(m.start, m.start.getMonth() === 0),
    value: monthEndMrr(m),
  }));
  const { multiplier } = scenarioMeta(scenario);
  const last = history[history.length - 1].value;
  const monthlyNetNew = (DAILY[LAST].mrr - DAILY[LAST - 90].mrr) / 3;
  const lastMonth = MONTHS[MONTHS.length - 1].start;

  const projection: Forecast["projection"] = [];
  const band: Forecast["band"] = [];
  let v = last;
  for (let k = 1; k <= HORIZON; k++) {
    const month = addMonths(lastMonth, k);
    v += monthlyNetNew * multiplier * (1 + PACE_GROWTH * k);
    projection.push({ label: monthLabel(month, month.getMonth() === 0), value: v });
    const spread = last * 0.011 * k ** 0.85;
    band.push([v - spread, v + spread]);
  }
  return { scenario, history, projection, band };
}

export const forecastEnd = (f: Forecast) => f.projection[f.projection.length - 1].value;

/** First projected month (1-based) at or above a target, or null if not reached within the horizon. */
export function monthsToTarget(f: Forecast, target: number): number | null {
  const i = f.projection.findIndex((p) => p.value >= target);
  return i === -1 ? null : i + 1;
}

export interface ForecastRow {
  month: string;
  low: number;
  projected: number;
  high: number;
  netNew: number;
  runRateArr: number;
}

export function forecastTable(f: Forecast): ForecastRow[] {
  let prev = f.history[f.history.length - 1].value;
  return f.projection.map((p, i) => {
    const row = {
      month: p.label,
      low: f.band[i][0],
      projected: p.value,
      high: f.band[i][1],
      netNew: p.value - prev,
      runRateArr: p.value * 12,
    };
    prev = p.value;
    return row;
  });
}
