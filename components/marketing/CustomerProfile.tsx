import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { PROFILE, STATUS_TONE } from "@/lib/data/customers";

export function CustomerProfile() {
  return (
    <div className="card-vis">
      <div className="ph">
        <span className="av" style={{ width: 34, height: 34, fontSize: 13 }}>
          {PROFILE.initials}
        </span>
        <div>
          <h4 style={{ margin: 0 }}>{PROFILE.name}</h4>
          <span className="muted" style={{ fontSize: 12.5 }}>
            {PROFILE.plan}
          </span>
        </div>
        <StatusBadge tone={STATUS_TONE[PROFILE.status]} className="r">
          {PROFILE.status}
        </StatusBadge>
      </div>
      <div className="stat-row" style={{ margin: "6px 0 18px" }}>
        {PROFILE.stats.map((s) => (
          <div key={s.label}>
            <small>{s.label}</small>
            <b>{s.value}</b>
          </div>
        ))}
      </div>
      <ul className="timeline">
        {PROFILE.timeline.map((e) => (
          <li key={e.date}>
            <time>{e.date}</time>
            <i style={{ background: e.color }} />
            <div>
              <b>{e.title}</b>
              <span>{e.detail}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
