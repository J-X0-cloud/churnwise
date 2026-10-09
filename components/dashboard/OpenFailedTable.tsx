import { money } from "@/lib/format";
import type { OpenFailedPayment } from "@/types/revenue";

import { DataTable } from "./DataTable";
import type { Column } from "./DataTable";
import { StatusBadge } from "./StatusBadge";

const columns = (maxAttempts: number): Column<OpenFailedPayment>[] => [
  { key: "customer", header: "Customer", render: (p) => <b>{p.customer}</b> },
  { key: "amount", header: "Amount", numeric: true, render: (p) => money(p.amount) },
  { key: "reason", header: "Decline reason", render: (p) => p.reason },
  { key: "attempts", header: "Attempts", numeric: true, render: (p) => `${p.attempts} of ${maxAttempts}` },
  { key: "next", header: "Next retry", render: (p) => p.nextRetry },
  {
    key: "step",
    header: "Recovery step",
    render: (p) => <StatusBadge tone={p.attempts >= 3 ? "warn" : "ok"}>{p.step}</StatusBadge>,
  },
];

export function OpenFailedTable({
  payments,
  maxAttempts,
}: {
  payments: OpenFailedPayment[];
  maxAttempts: number;
}) {
  return <DataTable columns={columns(maxAttempts)} rows={payments} rowKey={(p) => p.customer} />;
}
