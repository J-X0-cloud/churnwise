import { REMINDER_SEQUENCE } from "@/lib/data/recovery";

export function ReminderSequence() {
  return (
    <div className="seq">
      {REMINDER_SEQUENCE.map((m) => (
        <div key={m.day} className="mail">
          <span className="day">{m.day}</span>
          <div>
            <b>{m.subject}</b>
            <span>{m.preview}</span>
          </div>
          <span className={m.state === "Opened" ? "pill g" : "pill"}>{m.state}</span>
        </div>
      ))}
    </div>
  );
}
