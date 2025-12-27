import { RECENT_ACTIVITY } from "@/lib/data/customers";

export function ActivityFeed() {
  return (
    <ul className="feed">
      {RECENT_ACTIVITY.map((item) => (
        <li key={item.customer + item.detail}>
          <span className="fi" style={{ background: item.color }}>
            {item.glyph}
          </span>
          <div>
            <b>{item.customer}</b>
            <small>
              {item.detail} · {item.when}
            </small>
          </div>
          <span className={`amt ${item.direction}`}>{item.amount}</span>
        </li>
      ))}
    </ul>
  );
}
