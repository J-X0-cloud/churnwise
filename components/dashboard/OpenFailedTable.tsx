import { MAX_ATTEMPTS, OPEN_FAILED } from "@/lib/data/recovery";
import type { OpenFailedPayment } from "@/lib/data/recovery";
import { money } from "@/lib/format";

import { DataTable } from "./DataTable";
import type { Column } from "./DataTable";
import { StatusBadge } from "./StatusBadge";

const COLUMNS: Column<OpenFailedPayment>[] = [
  { key: "customer", header: "Customer", render: (p) => <b>{p.customer}</b> },
  { key: "amount", header: "Amount", numeric: true, render: (p) => money(p.amount) },
  { key: "reason", header: "Decline reason", render: (p) => p.reason },
  { key: "attempts", header: "Attempts", numeric: true, render: (p) => `${p.attempts} of ${MAX_ATTEMPTS}` },
  { key: "next", header: "Next retry", render: (p) => p.nextRetry },
  {
    key: "step",
    header: "Recovery step",
    render: (p) => <StatusBadge tone={p.attempts >= 3 ? "warn" : "ok"}>{p.step}</StatusBadge>,
  },
];

export function OpenFailedTable() {
  return <DataTable columns={COLUMNS} rows={OPEN_FAILED} rowKey={(p) => p.customer} />;
}
