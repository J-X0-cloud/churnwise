import Link from "next/link";

import { FOOTER_COLUMNS, TAGLINE } from "@/lib/data/site";

import { Brand } from "./Logo";

export function Footer() {
  return (
    <footer className="foot">
      <div className="wrap">
        <div className="foot-grid">
          <div className="foot-brand">
            <Brand />
            <p>{TAGLINE}</p>
            <a className="status" href="#">
              <i />
              All systems operational
            </a>
          </div>
          {FOOTER_COLUMNS.map((col) => (
            <div key={col.title}>
              <h4>{col.title}</h4>
              {col.links.map((link) =>
                link.href.startsWith("/") ? (
                  <Link key={link.label} href={link.href}>
                    {link.label}
                  </Link>
                ) : (
                  <a key={link.label} href={link.href}>
                    {link.label}
                  </a>
                ),
              )}
            </div>
          ))}
        </div>
        <div className="foot-base">
          <span>&copy; 2026 Churnwise, Inc. All rights reserved.</span>
          <span>
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">DPA</a>
          </span>
        </div>
      </div>
    </footer>
  );
}
