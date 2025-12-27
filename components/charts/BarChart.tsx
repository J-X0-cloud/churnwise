"use client";

import { frame, niceTicks, plotWidth, yScale } from "@/lib/charts";
import { money, moneyAxis } from "@/lib/format";
import { BRAND } from "@/lib/palette";
import type { BarDatum } from "@/types/charts";

import { useTip } from "./TooltipProvider";

interface BarChartProps {
  data: BarDatum[];
  width?: number;
  height?: number;
  color?: string;
  label?: string;
}

/** Vertical bars with rounded tops. */
export function BarChart({
  data,
  width = 520,
  height = 200,
  color = BRAND,
  label = "Bar chart",
}: BarChartProps) {
  const tip = useTip();
  const f = frame(width, height, { left: 48, right: 8, top: 12, bottom: 26 });
  const ticks = niceTicks(0, Math.max(...data.map((d) => d.value)) * 1.05, 4);
  const y = yScale(f, 0, ticks[ticks.length - 1]);
  const bw = plotWidth(f) / data.length;
  const stride = Math.max(1, Math.round(data.length / 8));

  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
      {ticks.map((t) => (
        <g key={t}>
          <line className="grid" x1={f.left} x2={width - f.right} y1={y(t).toFixed(1)} y2={y(t).toFixed(1)} />
          <text className="ax" x={f.left - 7} y={(y(t) + 4).toFixed(1)} textAnchor="end">
            {moneyAxis(t)}
          </text>
        </g>
      ))}
      {data.map((d, i) => {
        const x = f.left + i * bw + bw * 0.18;
        const w = bw * 0.64;
        return (
          <g key={d.label}>
            <path
              d={`M${x.toFixed(1)},${y(0).toFixed(1)} V${(y(d.value) + 3).toFixed(1)} q0,-3 3,-3 h${(w - 6).toFixed(1)} q3,0 3,3 V${y(0).toFixed(1)}Z`}
              fill={color}
              {...tip(`${d.label}: ${money(d.value)}`)}
            />
            {i % stride === 0 ? (
              <text className="ax" x={(x + w / 2).toFixed(1)} y={height - 8} textAnchor="middle">
                {d.label}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}
