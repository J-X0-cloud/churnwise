"use client";

import { RANGES, RANGE_KEYS } from "@/lib/revenue";
import type { RangeKey } from "@/types/revenue";

import { Segmented } from "./Segmented";

const OPTIONS = RANGE_KEYS.map((key) => ({ key, label: RANGES[key].short }));

export function RangePicker({ value, onChange }: { value: RangeKey; onChange?: (range: RangeKey) => void }) {
  return <Segmented options={OPTIONS} value={value} onChange={onChange} label="Date range" />;
}
