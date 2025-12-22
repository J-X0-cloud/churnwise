export interface LinePoint {
  /** Empty string hides the x label for this point. */
  label: string;
  value: number | null;
  /** Tooltip title; defaults to the label. */
  tip?: string;
}

export interface OverlayLine {
  values: Array<number | null>;
  color: string;
  dash: string;
}

export type AxisFormat = "money" | "percent0";

export interface BarDatum {
  label: string;
  value: number;
}

export interface LegendEntry {
  label: string;
  color: string;
  kind?: "box" | "line" | "band";
}
