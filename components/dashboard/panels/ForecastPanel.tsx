"use client";

import { ForecastChart } from "@/components/charts/ForecastChart";
import { HBarList } from "@/components/charts/HBarList";
import { Legend } from "@/components/charts/Legend";
import { money, pct } from "@/lib/format";
import { INK, SCENARIO_COLORS } from "@/lib/palette";
import type { ForecastRow, ForecastView, Scenario } from "@/types/revenue";

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

interface ForecastPanelProps {
  forecast: ForecastView;
  scenario: Scenario;
  onScenarioChange: (s: Scenario) => void;
}

export function ForecastPanel({ forecast, scenario, onScenarioChange }: ForecastPanelProps) {
  const { scenarios } = forecast;
  const meta = scenarios.find((s) => s.key === scenario)!;
  const current = meta.forecast;
  const color = SCENARIO_COLORS[scenario];
  const end = meta.end;
  const [low, high] = current.band[current.band.length - 1];
  const assumptions = meta.assumptions;
  const scenarioName = meta.label.toLowerCase();
  const endOf = (key: Scenario) => scenarios.find((s) => s.key === key)!.end;

  return (
    <>
      <div className="filters">
        <Segmented
          options={scenarios.map((s) => ({ key: s.key, label: s.label }))}
          value={scenario}
          onChange={onScenarioChange}
          label="Scenario"
        />
        <span className="chip">
          Horizon: <b>{forecast.horizonMonths} months</b>
        </span>
      </div>
      <div className="dg dg-21">
        <Panel
          title={`MRR forecast · ${scenarioName} scenario`}
          meta={`next ${forecast.horizonMonths} months · 80% interval`}
        >
          <div className="cs-wide">
            <ForecastChart forecast={current} width={900} height={320} />
          </div>
          <Legend
            items={[
              { label: "Actual", color: INK, kind: "line" },
              { label: `Forecast (${scenarioName})`, color, kind: "line" },
              { label: "80% interval", color, kind: "band" },
            ]}
          />
        </Panel>
        <Panel title={forecast.horizonLabel}>
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
              <b>{pct((end / forecast.currentMrr - 1) * 100, 0, true)}</b>
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
            <DataTable columns={COLUMNS} rows={meta.table} rowKey={(r) => r.month} />
          </div>
        </Panel>
        <Panel title="Scenarios compared" meta={`MRR in ${forecast.horizonShortLabel}`}>
          <HBarList
            items={scenarios.map((s) => [s.label, s.end])}
            color={color}
            format={(v) => money(v, 2)}
          />
          <p className="note">
            Scenarios share the same history and differ only in new-business pace, expansion and churn
            assumptions. Edit any assumption to save a custom scenario.
          </p>
          <div className="stat-row" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <small>Spread, stretch vs conservative</small>
              <b>{money(endOf("stretch") - endOf("conservative"))}</b>
            </div>
            <div>
              <small>Months to {money(forecast.target, 0)} MRR</small>
              <b>{meta.monthsToTarget ?? `${forecast.horizonMonths}+`}</b>
            </div>
          </div>
        </Panel>
      </div>
    </>
  );
}
