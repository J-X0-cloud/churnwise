import type { ReactNode } from "react";

import { STATUS_GLYPH } from "./status";
import type { StatusTone } from "./status";

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
