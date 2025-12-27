"use client";

import { useMemo } from "react";

import { MovementChart } from "@/components/charts/MovementChart";
import { Waterfall } from "@/components/charts/Waterfall";
import { money } from "@/lib/format";
import { MOVEMENTS } from "@/lib/palette";
import { movementBuckets, rangeStats, sumTotals } from "@/lib/revenue";
import { DAILY } from "@/lib/data/simulation";
import type { MovementBucket, RangeKey } from "@/types/revenue";

import { DataTable } from "../DataTable";
import type { Column } from "../DataTable";
import { MovementLegend } from "../MovementLegend";
import { Panel } from "../Panel";

const COLUMNS: Column<MovementBucket>[] = [
  { key: "period", header: "Period", render: (b) => b.label },
  ...MOVEMENTS.map(
    (m): Column<MovementBucket> => ({
      key: m.key,
      header: (
        <>
          <i className="dot" style={{ background: m.color }} />
          {m.label}
        </>
      ),
      numeric: true,
      render: (b) => money(b[m.key]),
    }),
  ),
  { key: "net", header: "Net new", numeric: true, render: (b) => <b>{money(b.net)}</b> },
  { key: "ending", header: "Ending MRR", numeric: true, render: (b) => money(DAILY[b.end - 1].mrr) },
];

export function RevenuePanel({ range }: { range: RangeKey }) {
  const { stats, buckets, totals } = useMemo(() => {
    const b = movementBuckets(range);
    return { stats: rangeStats(range), buckets: b, totals: sumTotals(b) };
  }, [range]);

  return (
    <>
      <div className="dg dg-12">
        <Panel title="MRR bridge" meta={stats.label}>
          <Waterfall
            start={stats.mrrStart}
            totals={totals}
            end={stats.mrr}
            width={440}
            height={320}
            compact
          />
        </Panel>
        <Panel title="New vs lost MRR" meta={stats.label}>
          <div className="cs-wide">
            <MovementChart buckets={buckets} width={820} height={300} />
          </div>
          <MovementLegend />
        </Panel>
      </div>
      <Panel
        title="Movement detail"
        meta="newest first"
        aside={
          <a className="chip r" href="#">
            Export CSV
          </a>
        }
      >
        <div className="scroll-x" style={{ maxHeight: 440, overflowY: "auto" }}>
          <DataTable
            columns={COLUMNS}
            rows={[...buckets].reverse()}
            rowKey={(b) => `${b.start}`}
            footer={
              <tr className="tot">
                <td>
                  <b>Total</b>
                </td>
                {MOVEMENTS.map((m) => (
                  <td key={m.key} className="n">
                    <b>{money(totals[m.key])}</b>
                  </td>
                ))}
                <td className="n">
                  <b>{money(buckets.reduce((s, b) => s + b.net, 0))}</b>
                </td>
                <td />
              </tr>
            }
          />
        </div>
      </Panel>
    </>
  );
}
