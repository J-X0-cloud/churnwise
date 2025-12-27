"use client";

import { useCallback, useEffect, useState } from "react";

import { Brand } from "@/components/site/Logo";
import { WORKSPACE } from "@/lib/data/simulation";
import type { CohortMetric, RangeKey, Scenario, TabKey } from "@/types/revenue";

import { AppNav, MobileTabs } from "./AppNav";
import { CustomersPanel } from "./panels/CustomersPanel";
import { ForecastPanel } from "./panels/ForecastPanel";
import { OverviewPanel } from "./panels/OverviewPanel";
import { RecoveryPanel } from "./panels/RecoveryPanel";
import { RetentionPanel } from "./panels/RetentionPanel";
import { RevenuePanel } from "./panels/RevenuePanel";
import { RangePicker } from "./RangePicker";
import { TABS, isTabKey } from "./tabs";

/**
 * The demo dashboard. The active tab lives in the URL hash (so /demo#recovery deep-links), while the
 * date range, cohort metric and forecast scenario are view state shared across tabs.
 */
export function DashboardShell() {
  const [tab, setTab] = useState<TabKey>("overview");
  const [range, setRange] = useState<RangeKey>("12m");
  const [cohortMetric, setCohortMetric] = useState<CohortMetric>("net");
  const [scenario, setScenario] = useState<Scenario>("base");

  useEffect(() => {
    const sync = () => {
      const hash = window.location.hash.slice(1);
      setTab(isTabKey(hash) ? hash : "overview");
    };
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  const navigate = useCallback((next: TabKey) => {
    window.history.replaceState(null, "", `#${next}`);
    setTab(next);
    window.scrollTo(0, 0);
  }, []);

  const title = TABS.find((t) => t.key === tab)!.title;

  return (
    <>
      <MobileTabs active={tab} onSelect={navigate} />
      <div className="dapp">
        <aside className="app-side">
          <Brand />
          <div className="ws">
            <b>{WORKSPACE.name}</b>
            <small>Sample workspace · {WORKSPACE.currency}</small>
          </div>
          <AppNav active={tab} onSelect={navigate} />
          <div className="side-foot">
            <b>Data synced 6 min ago</b>
            {WORKSPACE.sources}
          </div>
        </aside>
        <main className="dmain" id="main">
          <div className="dtop">
            <h1>
              <span>{title}</span>
              <span className="sub">
                {WORKSPACE.name} · all plans · {WORKSPACE.currency}
              </span>
            </h1>
            <div className="tools">
              <RangePicker value={range} onChange={setRange} />
              <span className="chip">
                Compare: <b>previous period</b>
              </span>
              <a className="chip" href="#">
                Segment: <b>All customers</b>
              </a>
              <a className="chip" href="#">
                Export
              </a>
            </div>
          </div>
          <section className="tabpane" id={tab} aria-label={title}>
            {tab === "overview" ? <OverviewPanel range={range} onNavigate={navigate} /> : null}
            {tab === "revenue" ? <RevenuePanel range={range} /> : null}
            {tab === "retention" ? (
              <RetentionPanel cohortMetric={cohortMetric} onCohortMetricChange={setCohortMetric} />
            ) : null}
            {tab === "customers" ? <CustomersPanel /> : null}
            {tab === "forecast" ? <ForecastPanel scenario={scenario} onScenarioChange={setScenario} /> : null}
            {tab === "recovery" ? <RecoveryPanel /> : null}
          </section>
        </main>
      </div>
    </>
  );
}
