import { INTEGRATIONS } from "@/lib/data/home";

export function Integrations() {
  return (
    <div className="integr">
      {INTEGRATIONS.map((i) => (
        <div key={i.name} className="int">
          <span className="mono" style={{ background: i.color }}>
            {i.mono}
          </span>
          <div>
            <b>{i.name}</b>
            <small>{i.kind}</small>
          </div>
        </div>
      ))}
    </div>
  );
}
