"use client";

import { useId } from "react";

import { frame, labelStride, linePath, niceTicks, plotHeight, plotWidth, xAt, yScale } from "@/lib/charts";
import { money, moneyAxis } from "@/lib/format";
import { BRAND } from "@/lib/palette";
import type { AxisFormat, LinePoint, OverlayLine } from "@/types/charts";

import { useTip } from "./TooltipProvider";

const FORMAT: Record<AxisFormat, { axis: (v: number) => string; tip: (v: number) => string }> = {
  money: { axis: moneyAxis, tip: money },
  percent0: { axis: (v) => `${v.toFixed(0)}%`, tip: (v) => `${v.toFixed(0)}%` },
};

export interface AreaChartProps {
  points: LinePoint[];
  width?: number;
  height?: number;
  color?: string;
  format?: AxisFormat;
  zero?: boolean;
  labelEvery?: number;
  overlays?: OverlayLine[];
  padLeft?: number;
  showEnd?: boolean;
  area?: boolean;
  label?: string;
}

/**
 * Line chart with an optional gradient area, overlay lines and a per-point hover layer (crosshair and
 * dot via CSS :hover, value via the shared tooltip).
 */
export function AreaChart({
  points,
  width = 760,
  height = 260,
  color = BRAND,
  format = "money",
  zero = false,
  labelEvery,
  overlays = [],
  padLeft = 54,
  showEnd = true,
  area = true,
  label = "Line chart",
}: AreaChartProps) {
  const gradientId = `g${useId().replace(/:/g, "")}`;
  const tip = useTip();
  const f = frame(width, height, { left: padLeft });
  const fmt = FORMAT[format];

  const values = points.map((p) => p.value);
  const all = [...values, ...overlays.flatMap((o) => o.values)].filter((v): v is number => v !== null);
  const ticks = niceTicks(zero ? 0 : Math.min(...all) * 0.96, Math.max(...all) * 1.02);
  const y = yScale(f, ticks[0], ticks[ticks.length - 1]);
  const n = points.length;
  const x = xAt(f, n);
  const stride = labelStride(n, labelEvery);
  const first = values.findIndex((v) => v !== null);
  const last = values.length - 1 - [...values].reverse().findIndex((v) => v !== null);
  const path = linePath(values, x, y);
  const cellWidth = plotWidth(f) / Math.max(1, n - 1);

  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity={0.22} />
          <stop offset="1" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      {ticks.map((t) => (
        <g key={t}>
          <line className="grid" x1={f.left} x2={width - f.right} y1={y(t).toFixed(1)} y2={y(t).toFixed(1)} />
          <text className="ax" x={f.left - 8} y={(y(t) + 4).toFixed(1)} textAnchor="end">
            {fmt.axis(t)}
          </text>
        </g>
      ))}
      {points.map((p, i) =>
        p.label && i % stride === 0 ? (
          <text key={`x${i}`} className="ax" x={x(i).toFixed(1)} y={height - 8} textAnchor="middle">
            {p.label}
          </text>
        ) : null,
      )}
      {area ? (
        <path
          d={`${path} L${x(last).toFixed(1)},${y(y.lo).toFixed(1)} L${x(first).toFixed(1)},${y(y.lo).toFixed(1)}Z`}
          fill={`url(#${gradientId})`}
        />
      ) : null}
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {overlays.map((o) => (
        <path
          key={o.color}
          d={linePath(o.values, x, y)}
          fill="none"
          stroke={o.color}
          strokeWidth={2}
          strokeDasharray={o.dash}
          strokeLinecap="round"
        />
      ))}
      {showEnd ? (
        <circle
          cx={x(last).toFixed(1)}
          cy={y(values[last]!).toFixed(1)}
          r={4.5}
          fill={color}
          stroke="#fff"
          strokeWidth={2}
        />
      ) : null}
      {points.map((p, i) =>
        p.value === null ? null : (
          <g key={`h${i}`} className="hp">
            <rect
              x={(x(i) - cellWidth / 2).toFixed(1)}
              y={f.top}
              width={cellWidth.toFixed(1)}
              height={plotHeight(f)}
              fill="transparent"
              {...tip(`${p.tip ?? p.label}: ${fmt.tip(p.value)}`)}
            />
            <line
              className="xh"
              x1={x(i).toFixed(1)}
              x2={x(i).toFixed(1)}
              y1={f.top}
              y2={height - f.bottom}
            />
            <circle
              className="xh"
              cx={x(i).toFixed(1)}
              cy={y(p.value).toFixed(1)}
              r={4}
              fill={color}
              stroke="#fff"
              strokeWidth={2}
            />
          </g>
        ),
      )}
    </svg>
  );
}
