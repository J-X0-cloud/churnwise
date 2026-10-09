"use client";

import type { RangeDefinition, RangeKey } from "@/types/revenue";

import { Segmented } from "./Segmented";

interface RangePickerProps {
  ranges: RangeDefinition[];
  value: RangeKey;
  onChange?: (range: RangeKey) => void;
}

export function RangePicker({ ranges, value, onChange }: RangePickerProps) {
  const options = ranges.map((r) => ({ key: r.key, label: r.short }));
  return <Segmented options={options} value={value} onChange={onChange} label="Date range" />;
}
