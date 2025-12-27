"use client";

import clsx from "clsx";

import { useTip } from "@/components/charts/TooltipProvider";
import { HEAT_DOMAIN, heatColor } from "@/lib/charts";
import { money } from "@/lib/format";
import { cohortAverage } from "@/lib/revenue";
import type { Cohort, CohortMetric } from "@/types/revenue";

interface CohortGridProps {
  cohorts: readonly Cohort[];
  metric?: CohortMetric;
  months?: number;
  rows?: number;
  /** Marketing variant: no size columns, whole-number cells. */
  compact?: boolean;
}

/** Retention heat map by signup month, with a cohort-average row. */
export function CohortGrid({
  cohorts,
  metric = "net",
  months = 12,
  rows = 12,
  compact = false,
}: CohortGridProps) {
  const tip = useTip();
  const shown = cohorts.slice(0, rows);
  const average = cohortAverage(cohorts, metric, months);
  const periods = Array.from({ length: months }, (_, k) => k);

  return (
    <table className={clsx("cohort", compact && "compact")}>
      <thead>
        <tr>
          <th>Cohort</th>
          {compact ? null : (
            <>
              <th>Customers</th>
              <th>Start MRR</th>
            </>
          )}
          {periods.map((k) => (
            <th key={k}>M{k}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {shown.map((c) => (
          <tr key={c.label}>
            <th scope="row">{c.label}</th>
            {compact ? null : (
              <>
                <td className="n">{c.customers}</td>
                <td className="n">{money(c.startMrr)}</td>
              </>
            )}
            {periods.map((k) => {
              const v = c[metric][k];
              if (v === undefined) return <td key={k} className="e" />;
              const { background, color } = heatColor(v, HEAT_DOMAIN[metric]);
              return (
                <td
                  key={k}
                  className="h"
                  style={{ background, color }}
                  {...tip(`${c.label} cohort · month ${k}: ${v.toFixed(1)}%`)}
                >
                  {v.toFixed(0)}
                  {compact ? "" : "%"}
                </td>
              );
            })}
          </tr>
        ))}
        <tr className="avg">
          <th scope="row">Average</th>
          {compact ? null : (
            <>
              <td />
              <td />
            </>
          )}
          {average.map((v, k) => (
            <td key={k} className={v === null ? undefined : "n"}>
              {v === null ? null : `${v.toFixed(0)}%`}
            </td>
          ))}
        </tr>
      </tbody>
    </table>
  );
}
