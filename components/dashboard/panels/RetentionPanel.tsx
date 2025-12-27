"use client";

import { useMemo } from "react";

import { AreaChart } from "@/components/charts/AreaChart";
import { HBarList } from "@/components/charts/HBarList";
import { Legend } from "@/components/charts/Legend";
import { CANCELLATION_REASONS } from "@/lib/data/customers";
import { COHORTS } from "@/lib/data/cohorts";
import { retentionKpis, retentionSeries } from "@/lib/metrics";
import { BLUE, RED } from "@/lib/palette";
import type { CohortMetric } from "@/types/revenue";

import { CohortGrid } from "../CohortGrid";
import { KpiGrid } from "../KpiTile";
import { Panel } from "../Panel";
import { Segmented } from "../Segmented";

const METRIC_OPTIONS: Array<{ key: CohortMetric; label: string }> = [
  { key: "net", label: "Net MRR" },
  { key: "logo", label: "Logos" },
];

interface RetentionPanelProps {
  cohortMetric: CohortMetric;
  onCohortMetricChange: (metric: CohortMetric) => void;
}

export function RetentionPanel({ cohortMetric, onCohortMetricChange }: RetentionPanelProps) {
  const series = useMemo(() => retentionSeries(), []);
  const kpis = useMemo(() => retentionKpis(), []);
  const [top1, , top3] = CANCELLATION_REASONS;

  return (
    <>
      <KpiGrid kpis={kpis} />
      <Panel
        title="Cohort retention"
        meta="monthly signup cohorts · darker = higher"
        style={{ marginBottom: 14 }}
        aside={
          <Segmented
            className="r"
            options={METRIC_OPTIONS}
            value={cohortMetric}
            onChange={onCohortMetricChange}
            label="Cohort metric"
          />
        }
      >
        <div className="scroll-x">
          <CohortGrid cohorts={COHORTS} metric={cohortMetric} />
        </div>
      </Panel>
      <div className="dg dg-11">
        <Panel title="NRR vs GRR" meta="trailing 12 months, by month">
          <div className="cs-wide">
            <AreaChart
              points={series.labels.map((label, i) => ({ label, value: series.nrr[i] }))}
              overlays={[{ values: series.grr, color: RED, dash: "0" }]}
              width={560}
              height={250}
              color={BLUE}
              format="percent0"
              labelEvery={2}
              padLeft={44}
              area={false}
              label="Net and gross revenue retention"
            />
          </div>
          <Legend
            items={[
              { label: "Net revenue retention", color: BLUE, kind: "line" },
              { label: "Gross revenue retention", color: RED, kind: "line" },
            ]}
          />
        </Panel>
        <Panel title="Why customers cancel" meta="cancellation survey · 12 months">
          <HBarList items={CANCELLATION_REASONS} color={RED} />
          <p className="note">
            {top1[0]} and {top3[0].toLowerCase()} together account for {top1[1] + top3[1]}% of cancellations,
            mostly on monthly Starter plans.
          </p>
        </Panel>
      </div>
    </>
  );
}
