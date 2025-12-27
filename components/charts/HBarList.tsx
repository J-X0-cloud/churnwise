interface HBarListProps {
  items: Array<[label: string, value: number]>;
  color: string;
  format?: (v: number) => string;
}

/** Ranked horizontal bars, scaled to the largest value. */
export function HBarList({ items, color, format = (v) => `${v.toFixed(0)}%` }: HBarListProps) {
  const max = Math.max(...items.map(([, v]) => v));
  return (
    <div className="hbars">
      {items.map(([label, value]) => (
        <div key={label} className="hb">
          <span className="hb-l">{label}</span>
          <span className="hb-t">
            <i style={{ width: `${((value / max) * 100).toFixed(1)}%`, background: color }} />
          </span>
          <b>{format(value)}</b>
        </div>
      ))}
    </div>
  );
}
