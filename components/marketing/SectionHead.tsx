import clsx from "clsx";
import type { CSSProperties, ReactNode } from "react";

interface SectionHeadProps {
  eyebrow?: string;
  title: ReactNode;
  lead?: string;
  centered?: boolean;
  titleStyle?: CSSProperties;
}

export function SectionHead({ eyebrow, title, lead, centered = false, titleStyle }: SectionHeadProps) {
  return (
    <div className={clsx("sec-head", centered && "c")}>
      {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
      <h2 style={titleStyle}>{title}</h2>
      {lead ? <p className="lead">{lead}</p> : null}
    </div>
  );
}
