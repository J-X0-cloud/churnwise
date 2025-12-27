import type { LegendEntry } from "@/types/charts";

export function Legend({ items }: { items: LegendEntry[] }) {
  return (
    <div className="legend">
      {items.map((item) => (
        <span key={item.label}>
          <i
            className={item.kind === "line" ? "ln" : undefined}
            style={{ background: item.color, opacity: item.kind === "band" ? 0.3 : undefined }}
          />
          {item.label}
        </span>
      ))}
    </div>
  );
}
