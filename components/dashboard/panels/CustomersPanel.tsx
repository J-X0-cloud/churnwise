"use client";

import { num } from "@/lib/format";
import type { CustomerAccount, CustomersView } from "@/types/revenue";

import { CustomersTable } from "../CustomersTable";
import { KpiGrid } from "../KpiTile";
import { Panel } from "../Panel";

const FILTERS = [
  ["Plan", "All"],
  ["Status", "All"],
  ["Owner", "Anyone"],
  ["Sort", "MRR, high to low"],
] as const;

export function CustomersPanel({
  customers,
  accounts,
}: {
  customers: CustomersView;
  accounts: CustomerAccount[];
}) {
  const { kpis } = customers;
  const total = num(customers.total);

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
