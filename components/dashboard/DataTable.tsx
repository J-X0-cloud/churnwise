import clsx from "clsx";
import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  header: ReactNode;
  numeric?: boolean;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  className?: string;
  /** Extra rows appended after the data (totals). */
  footer?: ReactNode;
}

export function DataTable<T>({ columns, rows, rowKey, className, footer }: DataTableProps<T>) {
  return (
    <table className={clsx("tbl", className)}>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.key} className={c.numeric ? "n" : undefined}>
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={rowKey(row, i)}>
            {columns.map((c) => (
              <td key={c.key} className={c.numeric ? "n" : undefined}>
                {c.render(row)}
              </td>
            ))}
          </tr>
        ))}
        {footer}
      </tbody>
    </table>
  );
}
