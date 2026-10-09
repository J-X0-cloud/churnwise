"use client";

import { useCallback, useEffect, useState } from "react";

import { Brand } from "@/components/site/Logo";
import type { CohortMetric, DashboardSnapshot, RangeKey, Scenario, TabKey } from "@/types/revenue";

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
 * date range, cohort metric and forecast scenario are view state shared across tabs. All numbers come from
 * one engine snapshot, so switching tabs or ranges never waits on the network.
 */
export function DashboardShell({ data }: { data: DashboardSnapshot }) {
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
  const { workspace } = data;

  return (
    <>
      <MobileTabs active={tab} onSelect={navigate} />
      <div className="dapp">
        <aside className="app-side">
          <Brand />
          <div className="ws">
            <b>{workspace.name}</b>
            <small>Sample workspace · {workspace.currency}</small>
          </div>
          <AppNav active={tab} onSelect={navigate} />
          <div className="side-foot">
            <b>Data synced 6 min ago</b>
            {workspace.sources}
          </div>
        </aside>
        <main className="dmain" id="main">
          <div className="dtop">
            <h1>
              <span>{title}</span>
              <span className="sub">
                {workspace.name} · all plans · {workspace.currency}
              </span>
            </h1>
            <div className="tools">
              <RangePicker ranges={data.ranges} value={range} onChange={setRange} />
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
            {tab === "overview" ? <OverviewPanel data={data} range={range} onNavigate={navigate} /> : null}
            {tab === "revenue" ? <RevenuePanel view={data.views[range]} /> : null}
            {tab === "retention" ? (
              <RetentionPanel
                retention={data.retention}
                cohortMetric={cohortMetric}
                onCohortMetricChange={setCohortMetric}
              />
            ) : null}
            {tab === "customers" ? (
              <CustomersPanel customers={data.customers} accounts={data.accounts} />
            ) : null}
            {tab === "forecast" ? (
              <ForecastPanel forecast={data.forecast} scenario={scenario} onScenarioChange={setScenario} />
            ) : null}
            {tab === "recovery" ? <RecoveryPanel recovery={data.recovery} /> : null}
          </section>
        </main>
      </div>
    </>
  );
}
