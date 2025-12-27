"use client";

import { useMemo } from "react";

import { ForecastChart } from "@/components/charts/ForecastChart";
import { HBarList } from "@/components/charts/HBarList";
import { Legend } from "@/components/charts/Legend";
import {
  SCENARIOS,
  SCENARIO_ASSUMPTIONS,
  forecast,
  forecastEnd,
  forecastTable,
  monthsToTarget,
  scenarioMeta,
} from "@/lib/forecast";
import type { ForecastRow } from "@/lib/forecast";
import { money, pct } from "@/lib/format";
import { INK } from "@/lib/palette";
import { DAILY, LAST } from "@/lib/data/simulation";
import type { Scenario } from "@/types/revenue";

import { DataTable } from "../DataTable";
import type { Column } from "../DataTable";
import { Panel } from "../Panel";
import { Segmented } from "../Segmented";

const COLUMNS: Column<ForecastRow>[] = [
  { key: "month", header: "Month", render: (r) => r.month },
  { key: "low", header: "Low (P10)", numeric: true, render: (r) => money(r.low) },
  { key: "projected", header: "Projected MRR", numeric: true, render: (r) => <b>{money(r.projected)}</b> },
  { key: "high", header: "High (P90)", numeric: true, render: (r) => money(r.high) },
  { key: "net", header: "Net new", numeric: true, render: (r) => `+${money(r.netNew)}` },
  { key: "arr", header: "Run-rate ARR", numeric: true, render: (r) => money(r.runRateArr) },
];

const MILLION = 1_000_000;

export function ForecastPanel({
  scenario,
  onScenarioChange,
}: {
  scenario: Scenario;
  onScenarioChange: (s: Scenario) => void;
}) {
  const all = useMemo(
    () =>
      Object.fromEntries(SCENARIOS.map((s) => [s.key, forecast(s.key)])) as Record<
        Scenario,
        ReturnType<typeof forecast>
      >,
    [],
  );
  const current = all[scenario];
  const meta = scenarioMeta(scenario);
  const end = forecastEnd(current);
  const [low, high] = current.band[current.band.length - 1];
  const assumptions = SCENARIO_ASSUMPTIONS[scenario];
  const scenarioName = meta.label.toLowerCase();

  return (
    <>
      <div className="filters">
        <Segmented
          options={SCENARIOS.map((s) => ({ key: s.key, label: s.label }))}
          value={scenario}
          onChange={onScenarioChange}
          label="Scenario"
        />
        <span className="chip">
          Horizon: <b>12 months</b>
        </span>
      </div>
      <div className="dg dg-21">
        <Panel title={`MRR forecast · ${scenarioName} scenario`} meta="next 12 months · 80% interval">
          <div className="cs-wide">
            <ForecastChart forecast={current} width={900} height={320} />
          </div>
          <Legend
            items={[
              { label: "Actual", color: INK, kind: "line" },
              { label: `Forecast (${scenarioName})`, color: meta.color, kind: "line" },
              { label: "80% interval", color: meta.color, kind: "band" },
            ]}
          />
        </Panel>
        <Panel title="September 2027">
          <div className="bignum">{money(end)}</div>
          <p className="muted" style={{ fontSize: 12.5, margin: "4px 0 0" }}>
            Projected MRR · range {money(low)} – {money(high)}
          </p>
          <div className="stat-row" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <small>Projected ARR</small>
              <b>{money(end * 12)}</b>
            </div>
            <div>
              <small>Growth vs today</small>
              <b>{pct((end / DAILY[LAST].mrr - 1) * 100, 0, true)}</b>
            </div>
          </div>
          <table className="tbl mini" style={{ marginTop: 14 }}>
            <thead>
              <tr>
                <th>Assumption</th>
                <th className="n">Monthly</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>New business MRR</td>
                <td className="n">{assumptions.newBusiness}</td>
              </tr>
              <tr>
                <td>Expansion rate</td>
                <td className="n">{assumptions.expansion}</td>
              </tr>
              <tr>
                <td>Cancelled MRR</td>
                <td className="n">{assumptions.cancelled}</td>
              </tr>
              <tr>
                <td>Reactivation</td>
                <td className="n">{assumptions.reactivation}</td>
              </tr>
            </tbody>
          </table>
        </Panel>
      </div>
      <div className="dg dg-21">
        <Panel
          title="Forecast by month"
          meta={`${scenarioName} scenario`}
          aside={
            <a className="chip r" href="#">
              Export CSV
            </a>
          }
        >
          <div className="scroll-x">
            <DataTable columns={COLUMNS} rows={forecastTable(current)} rowKey={(r) => r.month} />
          </div>
        </Panel>
        <Panel title="Scenarios compared" meta="MRR in Sep 2027">
          <HBarList
            items={SCENARIOS.map((s) => [s.label, forecastEnd(all[s.key])])}
            color={meta.color}
            format={(v) => money(v, 2)}
          />
          <p className="note">
            Scenarios share the same history and differ only in new-business pace, expansion and churn
            assumptions. Edit any assumption to save a custom scenario.
          </p>
          <div className="stat-row" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <small>Spread, stretch vs conservative</small>
              <b>{money(forecastEnd(all.stretch) - forecastEnd(all.conservative))}</b>
            </div>
            <div>
              <small>Months to $1M MRR</small>
              <b>{monthsToTarget(current, MILLION) ?? "12+"}</b>
            </div>
          </div>
        </Panel>
      </div>
    </>
  );
}
