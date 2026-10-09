import { STATUS_TONE } from "@/components/dashboard/status";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { TONES } from "@/lib/palette";
import type { CustomerProfile as Profile } from "@/types/revenue";

export function CustomerProfile({ profile }: { profile: Profile }) {
  return (
    <div className="card-vis">
      <div className="ph">
        <span className="av" style={{ width: 34, height: 34, fontSize: 13 }}>
          {profile.initials}
        </span>
        <div>
          <h4 style={{ margin: 0 }}>{profile.name}</h4>
          <span className="muted" style={{ fontSize: 12.5 }}>
            {profile.plan}
          </span>
        </div>
        <StatusBadge tone={STATUS_TONE[profile.status]} className="r">
          {profile.status}
        </StatusBadge>
      </div>
      <div className="stat-row" style={{ margin: "6px 0 18px" }}>
        {profile.stats.map((s) => (
          <div key={s.label}>
            <small>{s.label}</small>
            <b>{s.value}</b>
          </div>
        ))}
      </div>
      <ul className="timeline">
        {profile.timeline.map((e) => (
          <li key={e.date}>
            <time>{e.date}</time>
            <i style={{ background: TONES[e.tone] }} />
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
