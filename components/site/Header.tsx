"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_LINKS, TRIAL_URL } from "@/lib/data/site";

import { Brand } from "./Logo";

export function Header() {
  const pathname = usePathname();
  const links = NAV_LINKS.map((link) => (
    <Link key={link.href} href={link.href} aria-current={pathname === link.href ? "page" : undefined}>
      {link.label}
    </Link>
  ));

  return (
    <header className="top">
      <div className="wrap nav">
        <Brand />
        <nav className="links" aria-label="Main">
          {links}
        </nav>
        <div className="nav-cta">
          <a className="signin" href="#">
            Sign in
          </a>
          <a className="btn btn-sm" href={TRIAL_URL}>
            Start free trial
          </a>
        </div>
        <details className="burger">
          <summary aria-label="Menu">
            <span />
            <span />
            <span />
          </summary>
          <div className="drawer">
            {links}
            <a href="#">Sign in</a>
            <a className="btn" href={TRIAL_URL}>
              Start free trial
            </a>
          </div>
        </details>
      </div>
    </header>
  );
}
