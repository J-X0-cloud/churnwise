"use client";

import { useMemo } from "react";

import { num } from "@/lib/format";
import { customerKpis, topAccounts } from "@/lib/metrics";
import { DAILY, LAST } from "@/lib/data/simulation";

import { CustomersTable } from "../CustomersTable";
import { KpiGrid } from "../KpiTile";
import { Panel } from "../Panel";

const FILTERS = [
  ["Plan", "All"],
  ["Status", "All"],
  ["Owner", "Anyone"],
  ["Sort", "MRR, high to low"],
] as const;

export function CustomersPanel() {
  const kpis = useMemo(() => customerKpis(), []);
  const accounts = topAccounts();
  const total = num(DAILY[LAST].customers);

  return (
    <>
      <div className="filters">
        {FILTERS.map(([label, value]) => (
          <span key={label} className="chip">
            {label}: <b>{value}</b>
          </span>
        ))}
      </div>
      <KpiGrid kpis={kpis} />
      <Panel title="Customers" meta={`${accounts.length} of ${total}`}>
        <div className="scroll-x">
          <CustomersTable customers={accounts} />
        </div>
      </Panel>
    </>
  );
}
