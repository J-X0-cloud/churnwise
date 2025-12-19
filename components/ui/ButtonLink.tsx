import clsx from "clsx";
import Link from "next/link";
import type { CSSProperties, ReactNode } from "react";

interface ButtonLinkProps {
  href: string;
  variant?: "primary" | "ghost" | "light";
  arrow?: boolean;
  className?: string;
  style?: CSSProperties;
  children: ReactNode;
}

export function ButtonLink({
  href,
  variant = "primary",
  arrow = false,
  className,
  style,
  children,
}: ButtonLinkProps) {
  const cls = clsx("btn", variant === "ghost" && "btn-ghost", variant === "light" && "btn-light", className);
  const content = (
    <>
      {children}
      {arrow ? <span className="arr">&rarr;</span> : null}
    </>
  );
  return href.startsWith("/") ? (
    <Link className={cls} href={href} style={style}>
      {content}
    </Link>
  ) : (
    <a className={cls} href={href} style={style}>
      {content}
    </a>
  );
}
