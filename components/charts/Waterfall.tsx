"use client";

import { bridgeBars, bridgeDomain, frame, yScale } from "@/lib/charts";
import type { BridgeStep } from "@/lib/charts";
import { money } from "@/lib/format";
import { BRAND_DARK, INK, MOVEMENTS } from "@/lib/palette";
import type { MovementTotals } from "@/types/revenue";

import { useTip } from "./TooltipProvider";

interface WaterfallProps {
  start: number;
  totals: MovementTotals;
  end: number;
  width?: number;
  height?: number;
  /** Abbreviate the longer movement names for narrow panels. */
  compact?: boolean;
}

/** MRR bridge: starting MRR, the five movements as floating bars with connectors, ending MRR. */
export function Waterfall({
  start,
  totals,
  end,
  width = 520,
  height = 260,
  compact = false,
}: WaterfallProps) {
  const tip = useTip();
  const f = frame(width, height, { left: 8, right: 8, top: 26, bottom: 34 });
  const [lo, hi] = bridgeDomain(start, end, totals);
  const y = yScale(f, lo, hi);
  const steps: BridgeStep[] = [
    { label: "Start", value: start, color: null },
    ...MOVEMENTS.map((m) => ({ label: m.label, value: totals[m.key] * m.sign, color: m.color })),
    { label: "End", value: end, color: null },
  ];
  const bars = bridgeBars(steps, y);
  const n = bars.length;
  const bw = (width - f.left - f.right) / n;
  const shortLabel = (label: string) =>
    compact ? (MOVEMENTS.find((m) => m.label === label)?.short ?? label) : label;

  return (
    <svg className="chart wf" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="MRR waterfall">
      <line className="grid" x1={f.left} x2={width - f.right} y1={y(lo).toFixed(1)} y2={y(lo).toFixed(1)} />
      <text className="ax" x={f.left} y={11}>
        Axis starts at {money(lo, 0)}
      </text>
      {bars.map((bar, i) => {
        const x = f.left + i * bw + bw * 0.16;
        const w = bw * 0.68;
        const isTotal = bar.color === null;
        const valueText = isTotal
          ? money(bar.value)
          : `${bar.value >= 0 ? "+" : "−"}${money(Math.abs(bar.value))}`;
        const fill = isTotal ? (i === 0 ? INK : BRAND_DARK) : bar.color!;
        return (
          <g key={bar.label}>
            <rect
              x={x.toFixed(1)}
              y={bar.y1.toFixed(1)}
              width={w.toFixed(1)}
              height={Math.max(1.5, bar.y2 - bar.y1).toFixed(1)}
              rx={3}
              fill={fill}
              {...tip(`${bar.label}: ${valueText}`)}
            />
            {i < n - 1 ? (
              <line
                className="conn"
                x1={(x + w).toFixed(1)}
                x2={(i === 0 ? x + bw : f.left + (i + 1) * bw + bw * 0.16).toFixed(1)}
                y1={y(bar.runningTotal).toFixed(1)}
                y2={y(bar.runningTotal).toFixed(1)}
              />
            ) : null}
            <text className="val" x={(x + w / 2).toFixed(1)} y={(bar.y1 - 7).toFixed(1)} textAnchor="middle">
              {valueText}
            </text>
            <text className="ax" x={(x + w / 2).toFixed(1)} y={height - 12} textAnchor="middle">
              {shortLabel(bar.label)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
