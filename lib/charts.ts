/**
 * Chart geometry for the hand-rolled SVG charts. Charts draw in a fixed viewBox and scale with CSS,
 * so all coordinates here are in viewBox units.
 */
import { lerp } from "@/lib/random";
import type { MovementTotals } from "@/types/revenue";

export interface Frame {
  width: number;
  height: number;
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export const frame = (
  width: number,
  height: number,
  pad: Partial<Omit<Frame, "width" | "height">> = {},
): Frame => ({
  width,
  height,
  left: pad.left ?? 54,
  right: pad.right ?? 16,
  top: pad.top ?? 14,
  bottom: pad.bottom ?? 28,
});

export const plotWidth = (f: Frame) => f.width - f.left - f.right;
export const plotHeight = (f: Frame) => f.height - f.top - f.bottom;

/** Friendly axis ticks (1, 2, 2.5, 5 × 10ⁿ) covering [lo, hi]. */
export function niceTicks(lo: number, hi: number, count = 4): number[] {
  const raw = (hi - lo) / count;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((s) => s * mag).find((s) => s >= raw) ?? mag * 10;
  const ticks: number[] = [];
  for (let v = Math.floor(lo / step) * step; v <= hi + step * 0.001; v += step)
    ticks.push(Number(v.toFixed(8)));
  if (ticks[ticks.length - 1] < hi) ticks.push(ticks[ticks.length - 1] + step);
  return ticks;
}

export interface LinearScale {
  (v: number): number;
  lo: number;
  hi: number;
}

/** Map a value in [lo, hi] to a y coordinate inside the frame. */
export function yScale(f: Frame, lo: number, hi: number): LinearScale {
  const fn = ((v: number) => f.top + plotHeight(f) * (1 - (v - lo) / (hi - lo))) as LinearScale;
  fn.lo = lo;
  fn.hi = hi;
  return fn;
}

/** Point positions for n evenly spaced samples. */
export const xAt = (f: Frame, n: number) => (i: number) => f.left + plotWidth(f) * (i / (n > 1 ? n - 1 : 1));

/** SVG path through the non-null points; gaps are skipped (joined), which suits split actual/forecast series. */
export function linePath(
  values: Array<number | null>,
  x: (i: number) => number,
  y: (v: number) => number,
): string {
  return values
    .map((v, i) => (v === null ? null : [x(i), y(v)]))
    .filter((p): p is number[] => p !== null)
    .map(([px, py], j) => `${j === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`)
    .join(" ");
}

/** Label every `every`th point; defaults to about seven labels. */
export const labelStride = (n: number, every?: number) => every ?? Math.max(1, Math.round(n / 7));

/** Sparkline geometry inside a w×h box with 2px/3px padding. */
export function sparkPoints(values: number[], w: number, h: number): Array<[number, number]> {
  const lo = Math.min(...values);
  const hi = Math.max(...values) > lo ? Math.max(...values) : lo + 1;
  return values.map((v, i) => [
    2 + ((w - 4) * i) / (values.length - 1),
    3 + (h - 6) * (1 - (v - lo) / (hi - lo)),
  ]);
}

// ------------------------------------------------------------------ MRR bridge (waterfall)

export interface BridgeStep {
  label: string;
  /** Signed amount for movements, absolute MRR for the start and end bars. */
  value: number;
  color: string | null;
}

export interface BridgeBar extends BridgeStep {
  y1: number;
  y2: number;
  /** Running total after this step (connector height). */
  runningTotal: number;
}

export function bridgeDomain(start: number, end: number, totals: MovementTotals): [number, number] {
  const lo = niceTicks(Math.min(start, end) * 0.9, Math.min(start, end) * 0.9 * 1.01)[0];
  const hi = Math.max(end, start + totals.new + totals.expansion + totals.reactivation) * 1.03;
  return [lo, hi];
}

export function bridgeBars(steps: BridgeStep[], y: LinearScale): BridgeBar[] {
  let run = steps[0].value;
  return steps.map((step, i) => {
    if (step.color === null) {
      if (i === 0) run = step.value;
      return { ...step, y1: y(step.value), y2: y(y.lo), runningTotal: step.value };
    }
    const a = run;
    const b = run + step.value;
    run = b;
    return { ...step, y1: y(Math.max(a, b)), y2: y(Math.min(a, b)), runningTotal: b };
  });
}

// ------------------------------------------------------------------ cohort heat map

const HEAT_STOPS: Array<[number, [number, number, number]]> = [
  [0, [241, 248, 244]],
  [0.5, [125, 206, 168]],
  [1, [11, 78, 57]],
];

/** Sequential single-hue scale (pale mint → deep green); text flips to white on the darkest cells. */
export function heatColor(value: number, domain: [number, number]): { background: string; color: string } {
  const t = Math.max(0, Math.min(1, (value - domain[0]) / (domain[1] - domain[0])));
  let rgb = HEAT_STOPS[HEAT_STOPS.length - 1][1];
  for (let k = 0; k < HEAT_STOPS.length - 1; k++) {
    const [t0, c0] = HEAT_STOPS[k];
    const [t1, c1] = HEAT_STOPS[k + 1];
    if (t <= t1) {
      const u = (t - t0) / (t1 - t0);
      rgb = [0, 1, 2].map((j) => Math.round(lerp(c0[j], c1[j], u))) as [number, number, number];
      break;
    }
  }
  const hex = `#${rgb.map((c) => c.toString(16).padStart(2, "0")).join("")}`;
  return { background: hex, color: t > 0.7 ? "#fff" : "#0d1f1a" };
}

export const HEAT_DOMAIN: Record<"net" | "logo", [number, number]> = { net: [88, 110], logo: [72, 100] };
