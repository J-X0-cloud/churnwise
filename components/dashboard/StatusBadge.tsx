import type { ReactNode } from "react";

import { STATUS_GLYPH } from "@/lib/data/customers";
import type { StatusTone } from "@/lib/data/customers";

export function StatusBadge({
  tone,
  children,
  className,
}: {
  tone: StatusTone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={`st ${tone}${className ? ` ${className}` : ""}`}>
      <i>{STATUS_GLYPH[tone]}</i>
      {children}
    </span>
  );
}
