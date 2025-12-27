"use client";

import { frame, linePath, niceTicks, plotHeight, plotWidth, xAt, yScale } from "@/lib/charts";
import { forecastEnd, scenarioMeta } from "@/lib/forecast";
import { money, moneyAxis } from "@/lib/format";
import { INK } from "@/lib/palette";
import type { Forecast } from "@/types/revenue";

import { useTip } from "./TooltipProvider";

/**
 * Actual MRR (solid, ink) joined to the projected MRR (dashed, scenario colour) with the 80% interval
 * shaded and the forecast region tinted.
 */
export function ForecastChart({
  forecast,
  width = 760,
  height = 280,
}: {
  forecast: Forecast;
  width?: number;
  height?: number;
}) {
  const tip = useTip();
  const { color } = scenarioMeta(forecast.scenario);
  const f = frame(width, height);
  const { history, projection } = forecast;
  const points = [...history, ...projection];
  const lastActual = history[history.length - 1].value;
  const band: Array<[number, number]> = [[lastActual, lastActual], ...forecast.band];

  const all = [...points.map((p) => p.value), ...band.flat()];
  const ticks = niceTicks(Math.min(...all) * 0.96, Math.max(...all) * 1.02);
  const y = yScale(f, ticks[0], ticks[ticks.length - 1]);
  const n = points.length;
  const x = xAt(f, n);
  const split = x(history.length - 1);
  const bandOffset = n - band.length;

  const actual = [...history.map((p) => p.value), ...projection.map(() => null)];
  const projected = [...history.slice(0, -1).map(() => null), lastActual, ...projection.map((p) => p.value)];
  const bandTop = band.map(([, hi], i) => `${x(bandOffset + i).toFixed(1)},${y(hi).toFixed(1)}`);
  const bandBottom = band.map(([lo], i) => `${x(bandOffset + i).toFixed(1)},${y(lo).toFixed(1)}`).reverse();
  const end = forecastEnd(forecast);
  const cellWidth = plotWidth(f) / (n - 1);

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="MRR forecast with 80% interval"
    >
      {ticks.map((t) => (
        <g key={t}>
          <line className="grid" x1={f.left} x2={width - f.right} y1={y(t).toFixed(1)} y2={y(t).toFixed(1)} />
          <text className="ax" x={f.left - 8} y={(y(t) + 4).toFixed(1)} textAnchor="end">
            {moneyAxis(t)}
          </text>
        </g>
      ))}
      {points.map((p, i) =>
        i % 2 === 0 ? (
          <text key={`x${i}`} className="ax" x={x(i).toFixed(1)} y={height - 8} textAnchor="middle">
            {p.label}
          </text>
        ) : null,
      )}
      <polygon
        className="band"
        points={[...bandTop, ...bandBottom].join(" ")}
        fill={color}
        fillOpacity={0.13}
      />
      <rect
        x={split.toFixed(1)}
        y={f.top}
        width={(width - f.right - split).toFixed(1)}
        height={plotHeight(f)}
        fill={color}
        fillOpacity={0.035}
      />
      <line
        x1={split.toFixed(1)}
        x2={split.toFixed(1)}
        y1={f.top}
        y2={height - f.bottom}
        stroke="#8a9893"
        strokeDasharray="3 3"
      />
      <text className="ax" x={(split + 8).toFixed(1)} y={f.top + 12}>
        Forecast · 80% interval
      </text>
      <text className="ax" x={(split - 8).toFixed(1)} y={f.top + 12} textAnchor="end">
        Actual
      </text>
      <path d={linePath(actual, x, y)} fill="none" stroke={INK} strokeWidth={2.2} strokeLinejoin="round" />
      <circle
        cx={split.toFixed(1)}
        cy={y(lastActual).toFixed(1)}
        r={4.5}
        fill={INK}
        stroke="#fff"
        strokeWidth={2}
      />
      <circle
        cx={x(n - 1).toFixed(1)}
        cy={y(end).toFixed(1)}
        r={4.5}
        fill={color}
        stroke="#fff"
        strokeWidth={2}
      />
      <text className="val" x={(x(n - 1) - 8).toFixed(1)} y={(y(end) - 10).toFixed(1)} textAnchor="end">
        {money(end)}
      </text>
      <path
        d={linePath(projected, x, y)}
        fill="none"
        stroke={color}
        strokeWidth={2.2}
        strokeDasharray="6 4"
        strokeLinecap="round"
      />
      {points.map((p, i) => (
        <g key={`h${i}`} className="hp">
          <rect
            x={(x(i) - cellWidth / 2).toFixed(1)}
            y={f.top}
            width={cellWidth.toFixed(1)}
            height={plotHeight(f)}
            fill="transparent"
            {...tip(`${p.label}: ${money(p.value)}${i >= history.length ? " (projected)" : ""}`)}
          />
          <line className="xh" x1={x(i).toFixed(1)} x2={x(i).toFixed(1)} y1={f.top} y2={height - f.bottom} />
          <circle
            className="xh"
            cx={x(i).toFixed(1)}
            cy={y(p.value).toFixed(1)}
            r={4}
            fill={i >= history.length ? color : INK}
            stroke="#fff"
            strokeWidth={2}
          />
        </g>
      ))}
    </svg>
  );
}
