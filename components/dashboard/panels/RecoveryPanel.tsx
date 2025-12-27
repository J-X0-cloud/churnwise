"use client";

import { useMemo } from "react";

import { BarChart } from "@/components/charts/BarChart";
import { HBarList } from "@/components/charts/HBarList";
import { OutcomeFunnel } from "@/components/charts/OutcomeFunnel";
import { DECLINE_REASONS, OPEN_FAILED } from "@/lib/data/recovery";
import { recoveryKpis } from "@/lib/metrics";
import { BRAND, MINT } from "@/lib/palette";
import { recoveryByMonth, recoveryFunnel } from "@/lib/recovery";

import { KpiGrid } from "../KpiTile";
import { OpenFailedTable } from "../OpenFailedTable";
import { Panel } from "../Panel";

export function RecoveryPanel() {
  const { kpis, funnel, months } = useMemo(
    () => ({ kpis: recoveryKpis(), funnel: recoveryFunnel(), months: recoveryByMonth(12) }),
    [],
  );

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
          <HBarList items={DECLINE_REASONS} color={BRAND} />
        </Panel>
        <Panel title="In recovery now" meta={`${OPEN_FAILED.length} invoices`}>
          <div className="scroll-x">
            <OpenFailedTable />
          </div>
        </Panel>
      </div>
    </>
  );
}
