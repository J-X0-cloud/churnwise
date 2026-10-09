import { ACTIVITY_STYLE } from "@/lib/palette";
import type { ActivityItem } from "@/types/revenue";

export function ActivityFeed({ items }: { items: ActivityItem[] }) {
  return (
    <ul className="feed">
      {items.map((item) => (
        <li key={item.customer + item.detail}>
          <span className="fi" style={{ background: ACTIVITY_STYLE[item.kind].color }}>
            {ACTIVITY_STYLE[item.kind].glyph}
          </span>
          <div>
            <b>{item.customer}</b>
            <small>
              {item.detail} · {item.when}
            </small>
          </div>
          <span className={`amt ${item.amount >= 0 ? "p" : "m"}`}>{item.amountLabel}</span>
        </li>
      ))}
    </ul>
  );
}
