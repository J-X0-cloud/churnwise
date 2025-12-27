import type { MouseEvent } from "react";

import { Icon } from "@/components/ui/icons";
import type { TabKey } from "@/types/revenue";

import { TABS } from "./tabs";

interface AppNavProps {
  active: TabKey;
  /** Omit for static screenshots; links then point nowhere. */
  onSelect?: (tab: TabKey) => void;
}

/** Sidebar section links. Each is a real #hash link so tabs can be deep-linked (e.g. /demo#recovery). */
export function AppNav({ active, onSelect }: AppNavProps) {
  const click = (tab: TabKey) => (e: MouseEvent) => {
    e.preventDefault();
    onSelect?.(tab);
  };
  return (
    <>
      {TABS.map((t) => (
        <a
          key={t.key}
          href={onSelect ? `#${t.key}` : "#"}
          className={t.key === active ? "si on" : "si"}
          aria-current={t.key === active ? "page" : undefined}
          onClick={onSelect ? click(t.key) : undefined}
        >
          <Icon name={t.icon} />
          <span>{t.label}</span>
        </a>
      ))}
    </>
  );
}

export function MobileTabs({ active, onSelect }: { active: TabKey; onSelect: (tab: TabKey) => void }) {
  return (
    <nav className="mobtabs" aria-label="Dashboard sections">
      {TABS.map((t) => (
        <a
          key={t.key}
          href={`#${t.key}`}
          className={t.key === active ? "on" : undefined}
          onClick={(e) => {
            e.preventDefault();
            onSelect(t.key);
          }}
        >
          {t.label}
        </a>
      ))}
    </nav>
  );
}
