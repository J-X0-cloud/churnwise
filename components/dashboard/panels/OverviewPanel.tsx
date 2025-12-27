"use client";

import { useMemo } from "react";

import { AreaChart } from "@/components/charts/AreaChart";
import { MovementChart } from "@/components/charts/MovementChart";
import { Waterfall } from "@/components/charts/Waterfall";
import { money, pct } from "@/lib/format";
import { MRR_LABEL_EVERY, mrrLine, overviewKpis, planBreakdown, topAccounts } from "@/lib/metrics";
import { RANGES, gained, lost, movementBuckets, quickRatio, rangeStats, sumTotals } from "@/lib/revenue";
import type { RangeKey, TabKey } from "@/types/revenue";

import { ActivityFeed } from "../ActivityFeed";
import { CustomersTable } from "../CustomersTable";
import { KpiGrid } from "../KpiTile";
import { MovementLegend } from "../MovementLegend";
import { Panel } from "../Panel";
import { PlanMix } from "../PlanMix";

export function OverviewPanel({ range, onNavigate }: { range: RangeKey; onNavigate: (tab: TabKey) => void }) {
  const { stats, buckets, totals, kpis } = useMemo(() => {
    const b = movementBuckets(range);
    return { stats: rangeStats(range), buckets: b, totals: sumTotals(b), kpis: overviewKpis(range) };
  }, [range]);
  const plans = useMemo(() => planBreakdown(), []);
  const cadence = RANGES[range].bucket;

  return (
    <>
      <KpiGrid kpis={kpis} />
      <div className="dg dg-21">
        <Panel
          title="Monthly recurring revenue"
          meta={`${stats.label} · ${money(stats.mrrStart)} → ${money(stats.mrr)}`}
          aside={<span className="r pill g">{pct((stats.mrr / stats.mrrStart - 1) * 100, 1, true)}</span>}
        >
          <div className="cs-wide">
            <AreaChart
              points={mrrLine(stats)}
              width={820}
              height={330}
              labelEvery={MRR_LABEL_EVERY[range]}
              zero
              label="Monthly recurring revenue"
            />
          </div>
        </Panel>
        <Panel title="MRR bridge" meta={stats.label}>
          <Waterfall
            start={stats.mrrStart}
            totals={totals}
            end={stats.mrr}
            width={440}
            height={300}
            compact
          />
          <div className="stat-row">
            <div>
              <small>Quick ratio</small>
              <b>{quickRatio(totals).toFixed(1)}×</b>
            </div>
            <div>
              <small>Gained</small>
              <b>{money(gained(totals))}</b>
            </div>
            <div>
              <small>Lost</small>
              <b>{money(lost(totals))}</b>
            </div>
          </div>
        </Panel>
      </div>
      <div className="dg dg-21">
        <Panel title="MRR movements" meta={`by ${cadence}`}>
          <div className="cs-wide">
            <MovementChart buckets={buckets} width={820} height={260} />
          </div>
          <MovementLegend />
        </Panel>
        <Panel title="MRR by plan" meta="as of Sep 24, 2026">
          <PlanMix plans={plans} />
        </Panel>
      </div>
      <div className="dg dg-21">
        <Panel
          title="Top customers"
          meta="by MRR movement, last 30 days"
          aside={
            <a
              className="chip r"
              href="#customers"
              onClick={(e) => {
                e.preventDefault();
                onNavigate("customers");
              }}
            >
              View all
            </a>
          }
        >
          <div className="scroll-x">
            <CustomersTable customers={topAccounts(6)} compact />
          </div>
        </Panel>
        <Panel title="Recent activity" meta="live">
          <ActivityFeed />
        </Panel>
      </div>
    </>
  );
}
