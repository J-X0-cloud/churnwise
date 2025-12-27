import { AreaChart } from "@/components/charts/AreaChart";
import { Waterfall } from "@/components/charts/Waterfall";
import { mrrLine, overviewKpis } from "@/lib/metrics";
import { RANGES, RANGE_KEYS, movementBuckets, rangeStats, sumTotals } from "@/lib/revenue";
import { WORKSPACE } from "@/lib/data/simulation";

import { AppNav } from "./AppNav";
import { KpiGrid } from "./KpiTile";

/** Browser-framed screenshot of the Overview tab for the home page hero, rendered from live components. */
export function AppWindow() {
  const range = "12m";
  const stats = rangeStats(range);
  const totals = sumTotals(movementBuckets(range));

  return (
    <div className="win">
      <div className="win-bar">
        <span />
        <span />
        <span />
        <em>app.churnwise.com/quillstack/overview</em>
      </div>
      <div className="win-body">
        <div className="app mini">
          <aside className="app-side">
            <div className="ws">
              <b>{WORKSPACE.name}</b>
              <small>Sample workspace</small>
            </div>
            <AppNav active="overview" />
          </aside>
          <div className="app-main">
            <div className="app-top">
              <h3>Overview</h3>
              <div className="seg">
                {RANGE_KEYS.map((k) => (
                  <span key={k} className={k === range ? "on" : undefined}>
                    {RANGES[k].short}
                  </span>
                ))}
              </div>
            </div>
            <KpiGrid kpis={overviewKpis(range).slice(0, 4)} columns={4} />
            <div className="grid-a">
              <div className="panel">
                <div className="ph">
                  <h4>MRR</h4>
                  <span className="muted">Oct 2025 – Sep 2026</span>
                </div>
                <div className="cs">
                  <AreaChart
                    points={mrrLine(stats)}
                    width={640}
                    height={230}
                    labelEvery={1}
                    zero
                    label="Monthly recurring revenue"
                  />
                </div>
              </div>
              <div className="panel">
                <div className="ph">
                  <h4>MRR bridge</h4>
                  <span className="muted">12 months</span>
                </div>
                <Waterfall
                  start={stats.mrrStart}
                  totals={totals}
                  end={stats.mrr}
                  width={420}
                  height={268}
                  compact
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
