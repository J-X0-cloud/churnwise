"use client";

import clsx from "clsx";

interface SegmentedProps<K extends string> {
  options: Array<{ key: K; label: string }>;
  value: K;
  onChange?: (key: K) => void;
  label: string;
  className?: string;
}

/** Toggle-button group (aria-pressed), used for date range, cohort metric and forecast scenario. */
export function Segmented<K extends string>({
  options,
  value,
  onChange,
  label,
  className,
}: SegmentedProps<K>) {
  return (
    <div className={clsx("seg", className)} role="group" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.key}
          type="button"
          aria-pressed={o.key === value}
          onClick={onChange ? () => onChange(o.key) : undefined}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
