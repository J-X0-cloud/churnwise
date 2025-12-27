import type { Delta } from "@/types/revenue";

const CLASS = { good: "up", bad: "dn", neutral: "nt" } as const;

export function DeltaBadge({ delta }: { delta: Delta }) {
  return (
    <span className={`dl ${CLASS[delta.tone]}`}>
      {delta.arrow ? <i>{delta.arrow === "up" ? "▲" : "▼"}</i> : null}
      {delta.text}
    </span>
  );
}
