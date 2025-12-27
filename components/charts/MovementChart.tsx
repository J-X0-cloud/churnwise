"use client";

import { frame, niceTicks, plotHeight, plotWidth, yScale } from "@/lib/charts";
import { money, moneyAxis } from "@/lib/format";
import { INK, MOVEMENTS } from "@/lib/palette";
import type { MovementBucket } from "@/types/revenue";

import { useTip } from "./TooltipProvider";

const GAINS = MOVEMENTS.filter((m) => m.sign > 0);
const LOSSES = MOVEMENTS.filter((m) => m.sign < 0);

function describe(b: MovementBucket): string {
  return [
    b.label,
    `New ${money(b.new)}`,
    `Expansion ${money(b.expansion)}`,
    `Reactivation ${money(b.reactivation)}`,
    `Contraction -${money(b.contraction)}`,
    `Churn -${money(b.churn)}`,
    `Net ${money(b.net)}`,
  ].join(" · ");
}

/** Diverging stacked bars: gains above zero, losses below, with the net-new line on top. */
export function MovementChart({
  buckets,
  width = 760,
  height = 280,
}: {
  buckets: MovementBucket[];
  width?: number;
  height?: number;
}) {
  const tip = useTip();
  const f = frame(width, height, { top: 12 });
  const gains = buckets.map((b) => b.new + b.expansion + b.reactivation);
  const losses = buckets.map((b) => b.contraction + b.churn);
  const ticks = niceTicks(-Math.max(...losses) * 1.05, Math.max(...gains) * 1.05, 5);
  const y = yScale(f, ticks[0], ticks[ticks.length - 1]);
  const n = buckets.length;
  const bw = plotWidth(f) / n;
  const gap = Math.max(1.5, bw * 0.28);
  const barW = bw - gap;
  const stride = Math.max(1, Math.round(n / 8));
  const y0 = y(0);
  const cx = (i: number) => f.left + i * bw + bw / 2;
  const netPath = buckets
    .map((b, i) => `${i === 0 ? "M" : "L"}${cx(i).toFixed(1)},${y(b.net).toFixed(1)}`)
    .join(" ");
  const radius = Math.min(2, barW / 3).toFixed(1);

  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="MRR movements by period">
      {ticks.map((t) => (
        <g key={t}>
          <line
            className={Math.abs(t) < 1e-6 ? "grid zero" : "grid"}
            x1={f.left}
            x2={width - f.right}
            y1={y(t).toFixed(1)}
            y2={y(t).toFixed(1)}
          />
          <text className="ax" x={f.left - 8} y={(y(t) + 4).toFixed(1)} textAnchor="end">
            {moneyAxis(t)}
          </text>
        </g>
      ))}
      {buckets.map((b, i) => {
        const x = f.left + i * bw + gap / 2;
        let up = 0;
        let down = 0;
        return (
          <g key={`${b.label}-${i}`}>
            <g className="bar" {...tip(describe(b))}>
              {GAINS.map((m) => {
                const h = y0 - y(b[m.key]);
                const rect = (
                  <rect
                    key={m.key}
                    x={x.toFixed(1)}
                    y={(y0 - up - h + 1).toFixed(1)}
                    width={barW.toFixed(1)}
                    height={Math.max(0, h - 1).toFixed(1)}
                    rx={radius}
                    fill={m.color}
                  />
                );
                up += h;
                return rect;
              })}
              {LOSSES.map((m) => {
                const h = y0 - y(b[m.key]);
                const rect = (
                  <rect
                    key={m.key}
                    x={x.toFixed(1)}
                    y={(y0 + down + 1).toFixed(1)}
                    width={barW.toFixed(1)}
                    height={Math.max(0, h - 1).toFixed(1)}
                    rx={radius}
                    fill={m.color}
                  />
                );
                down += h;
                return rect;
              })}
              <rect
                x={(f.left + i * bw).toFixed(1)}
                y={f.top}
                width={bw.toFixed(1)}
                height={plotHeight(f)}
                fill="transparent"
              />
            </g>
            {i % stride === 0 ? (
              <text className="ax" x={cx(i).toFixed(1)} y={height - 8} textAnchor="middle">
                {b.label}
              </text>
            ) : null}
          </g>
        );
      })}
      <path d={netPath} fill="none" stroke={INK} strokeWidth={2} strokeLinejoin="round" />
      {n <= 24
        ? buckets.map((b, i) => (
            <circle
              key={`n${i}`}
              cx={cx(i).toFixed(1)}
              cy={y(b.net).toFixed(1)}
              r={3.2}
              fill={INK}
              stroke="#fff"
              strokeWidth={1.5}
            />
          ))
        : null}
    </svg>
  );
}
