import { RETRY_TIMELINE } from "@/lib/data/recovery";

export function RetryTimeline() {
  return (
    <div className="retry">
      {RETRY_TIMELINE.map((s) => (
        <div key={s.day} className={s.win ? "win-step" : undefined}>
          <small>{s.day}</small>
          <b>{s.title}</b>
          {s.body}
        </div>
      ))}
    </div>
  );
}
