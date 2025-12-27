import { sparkPoints } from "@/lib/charts";
import { BRAND } from "@/lib/palette";

interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  color?: string;
  fill?: boolean;
}

export function Sparkline({ values, width = 96, height = 28, color = BRAND, fill = true }: SparklineProps) {
  const pts = sparkPoints(values, width, height);
  const d = pts.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const [lx, ly] = pts[pts.length - 1];
  return (
    <svg
      className="spark"
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      aria-hidden="true"
    >
      {fill ? (
        <path d={`${d} L${lx.toFixed(1)},${height} L2,${height}Z`} fill={color} fillOpacity={0.12} />
      ) : null}
      <path d={d} fill="none" stroke={color} strokeWidth={1.6} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={lx.toFixed(1)} cy={ly.toFixed(1)} r={2.2} fill={color} />
    </svg>
  );
}
