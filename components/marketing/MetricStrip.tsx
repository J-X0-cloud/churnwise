import { METRIC_STRIP } from "@/lib/data/home";

export function MetricStrip() {
  return (
    <div className="metric-strip">
      {METRIC_STRIP.map((m) => (
        <div key={m.name}>
          <b>{m.name}</b>
          <p>{m.body}</p>
          <code>{m.formula}</code>
        </div>
      ))}
    </div>
  );
}
