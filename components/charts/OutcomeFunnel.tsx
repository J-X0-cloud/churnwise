import { money } from "@/lib/format";
import type { FunnelItem } from "@/types/revenue";

/** Failed-payment outcomes as bars relative to the total failed amount. */
export function OutcomeFunnel({ items }: { items: FunnelItem[] }) {
  const total = items[0].value;
  return (
    <div className="funnel">
      {items.map((item) => (
        <div key={item.label} className="fn">
          <div className="fn-h">
            <span>{item.label}</span>
            <b>{money(item.value)}</b>
          </div>
          <span className="fn-t">
            <i style={{ width: `${((item.value / total) * 100).toFixed(1)}%`, background: item.color }} />
          </span>
        </div>
      ))}
    </div>
  );
}
