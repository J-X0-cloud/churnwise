"use client";

import { BarChart } from "@/components/charts/BarChart";
import { HBarList } from "@/components/charts/HBarList";
import { OutcomeFunnel } from "@/components/charts/OutcomeFunnel";
import { BRAND, MINT } from "@/lib/palette";
import type { RecoveryView } from "@/types/revenue";

import { KpiGrid } from "../KpiTile";
import { OpenFailedTable } from "../OpenFailedTable";
import { Panel } from "../Panel";

export function RecoveryPanel({ recovery }: { recovery: RecoveryView }) {
  const { kpis, funnel, months, openFailed } = recovery;

  return (
    <>
      <KpiGrid kpis={kpis} />
      <div className="dg dg-11">
        <Panel title="Failed payment outcomes" meta="last 12 months">
          <OutcomeFunnel items={funnel.items} />
        </Panel>
        <Panel title="Recovered revenue by month">
          <div className="cs-wide">
            <BarChart
              data={months.map((m) => ({ label: m.label, value: m.recovered }))}
              width={620}
              height={230}
              color={MINT}
              label="Recovered revenue by month"
            />
          </div>
        </Panel>
      </div>
      <div className="dg dg-12">
        <Panel title="Decline reasons">
          <HBarList items={recovery.declineReasons} color={BRAND} />
        </Panel>
        <Panel title="In recovery now" meta={`${openFailed.length} invoices`}>
          <div className="scroll-x">
            <OpenFailedTable payments={openFailed} maxAttempts={recovery.maxAttempts} />
          </div>
        </Panel>
      </div>
    </>
  );
}
