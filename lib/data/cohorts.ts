/**
 * Monthly signup cohorts for the sample workspace (Oct 2025 – Sep 2026). Net MRR retention includes
 * expansion, so healthy cohorts climb back above 100%; logo retention can only fall.
 */
import { addMonths } from "date-fns";

import { monthYear } from "@/lib/dates";
import { createRng, lerp } from "@/lib/random";
import type { Cohort } from "@/types/revenue";

export const FIRST_COHORT = new Date(2025, 9, 1);
export const COHORT_COUNT = 12;

function generate(): Cohort[] {
  const rng = createRng(7);
  return Array.from({ length: COHORT_COUNT }, (_, ci) => {
    const month = addMonths(FIRST_COHORT, ci);
    const customers = Math.round(lerp(58, 84, ci / 11) + rng.uniform(-6, 6));
    const net = [100];
    const logo = [100];
    for (let k = 1; k < COHORT_COUNT - ci; k++) {
      net.push(100 - 7.5 * (1 - Math.exp(-k / 1.8)) + 1.45 * k + 0.35 * ci + rng.uniform(-1.2, 1.2));
      const lv = 100 - 12.5 * (1 - Math.exp(-k / 2.2)) - 0.55 * k + 0.25 * ci + rng.uniform(-1, 1);
      logo.push(Math.min(lv, logo[logo.length - 1] - 0.2));
    }
    return {
      month,
      label: monthYear(month),
      customers,
      startMrr: customers * lerp(292, 334, ci / 11),
      net,
      logo,
    };
  });
}

export const COHORTS: readonly Cohort[] = generate();
