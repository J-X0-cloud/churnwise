import { Sparkline } from "@/components/charts/Sparkline";
import { STATUS_TONE } from "@/lib/data/customers";
import { money } from "@/lib/format";
import { accountTrend } from "@/lib/metrics";
import { AMBER, BRAND, MUTED, RED } from "@/lib/palette";
import type { CustomerAccount } from "@/types/revenue";

import { DataTable } from "./DataTable";
import type { Column } from "./DataTable";
import { StatusBadge } from "./StatusBadge";

const TREND_COLOR = { up: BRAND, flat: MUTED, down: RED } as const;

const initials = (name: string) =>
  name
    .replace("&", "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("");

const healthColor = (h: number) => (h >= 75 ? BRAND : h >= 45 ? AMBER : RED);

type Row = CustomerAccount & { index: number };

const BASE_COLUMNS: Column<Row>[] = [
  {
    key: "customer",
    header: "Customer",
    render: (c) => (
      <>
        <span className="av">{initials(c.name)}</span>
        <b>{c.name}</b>
      </>
    ),
  },
  { key: "plan", header: "Plan", render: (c) => c.plan },
  { key: "mrr", header: "MRR", numeric: true, render: (c) => money(c.mrr) },
  {
    key: "trend",
    header: "12-month MRR",
    render: (c) => (
      <Sparkline values={accountTrend(c, c.index)} width={92} height={26} color={TREND_COLOR[c.trend]} />
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (c) => <StatusBadge tone={STATUS_TONE[c.status]}>{c.status}</StatusBadge>,
  },
  {
    key: "health",
    header: "Health",
    numeric: true,
    render: (c) => (
      <>
        <span className="hl">
          <i style={{ width: `${c.health}%`, background: healthColor(c.health) }} />
        </span>
        {c.health}
      </>
    ),
  },
];

const DETAIL_COLUMNS: Column<Row>[] = [
  { key: "since", header: "Customer since", render: (c) => c.since },
  { key: "owner", header: "Owner", render: (c) => c.owner },
];

export function CustomersTable({
  customers,
  compact = false,
}: {
  customers: CustomerAccount[];
  compact?: boolean;
}) {
  return (
    <DataTable
      className="cust"
      columns={compact ? BASE_COLUMNS : [...BASE_COLUMNS, ...DETAIL_COLUMNS]}
      rows={customers.map((c, index) => ({ ...c, index }))}
      rowKey={(c) => c.name}
    />
  );
}
