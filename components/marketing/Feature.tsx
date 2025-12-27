import clsx from "clsx";
import type { CSSProperties, ReactNode } from "react";

interface FeatureProps {
  id?: string;
  eyebrow: string;
  title: string;
  lead: string;
  reverse?: boolean;
  style?: CSSProperties;
  /** Copy under the lead: check lists, stats, links. */
  children?: ReactNode;
  /** The product visual. */
  visual: ReactNode;
}

export function Feature({
  id,
  eyebrow,
  title,
  lead,
  reverse = false,
  style,
  children,
  visual,
}: FeatureProps) {
  return (
    <div className={clsx("feature", reverse && "rev")} id={id} style={style}>
      <div className="f-copy">
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p className="lead">{lead}</p>
        {children}
      </div>
      {visual}
    </div>
  );
}
