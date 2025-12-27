import clsx from "clsx";
import type { CSSProperties, ReactNode } from "react";

interface PanelProps {
  /** `panel` inside the app, `card` for product visuals on marketing pages. */
  variant?: "panel" | "card";
  title?: ReactNode;
  meta?: ReactNode;
  /** Right-aligned element in the header: a pill, chip or segmented control. */
  aside?: ReactNode;
  className?: string;
  style?: CSSProperties;
  children: ReactNode;
}

export function Panel({ variant = "panel", title, meta, aside, className, style, children }: PanelProps) {
  return (
    <div className={clsx(variant === "card" ? "card-vis" : "panel", className)} style={style}>
      {title || meta || aside ? (
        <div className="ph">
          {title ? <h4>{title}</h4> : null}
          {meta ? <span className="muted">{meta}</span> : null}
          {aside}
        </div>
      ) : null}
      {children}
    </div>
  );
}
