import type { Metadata } from "next";

import { AreaChart } from "@/components/charts/AreaChart";
import { ForecastChart } from "@/components/charts/ForecastChart";
import { CohortGrid } from "@/components/dashboard/CohortGrid";
import { KpiGrid } from "@/components/dashboard/KpiTile";
import { Panel } from "@/components/dashboard/Panel";
import { CtaBand } from "@/components/marketing/CtaBand";
import { CustomerProfile } from "@/components/marketing/CustomerProfile";
import { DefinitionsTable } from "@/components/marketing/DefinitionsTable";
import { Feature } from "@/components/marketing/Feature";
import { IconCards } from "@/components/marketing/IconCards";
import { SectionHead } from "@/components/marketing/SectionHead";
import { SegmentBars } from "@/components/marketing/SegmentBars";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { CheckList } from "@/components/ui/CheckList";
import { COHORTS } from "@/lib/data/cohorts";
import { CAPABILITY_CARDS, PLATFORM_CARDS, PROFILE_CHECKS, SEGMENT_CHECKS } from "@/lib/data/product";
import { SCENARIOS, forecast, forecastEnd } from "@/lib/forecast";
import { money } from "@/lib/format";
import { mrrLine, overviewKpis } from "@/lib/metrics";
import { rangeStats } from "@/lib/revenue";

export const metadata: Metadata = {
  title: "Revenue analytics: MRR, cohorts & forecasting",
  description:
    "MRR movements, net revenue retention, cohort analysis, segmentation, customer profiles and forecasting for subscription businesses, rebuilt from raw billing events.",
};

const HERO_TITLE = { fontSize: "clamp(36px,4.6vw,58px)" };

export default function ProductPage() {
  const stats = rangeStats("12m");
  const forecasts = SCENARIOS.map((s) => ({ ...s, forecast: forecast(s.key) }));
  const base = forecasts.find((f) => f.key === "base")!.forecast;

  return (
    <>
      <section className="phero">
        <div className="wrap split">
          <div>
            <span className="eyebrow">Revenue analytics</span>
            <h1 style={HERO_TITLE}>Subscription metrics you don&apos;t have to double-check.</h1>
            <p className="lead">
              Churnwise rebuilds your revenue history from raw billing events, so every chart can be traced
              back to an invoice. Then it slices that history any way your team needs.
            </p>
            <div className="hero-cta">
              <ButtonLink href="/demo" arrow>
                Open the live demo
              </ButtonLink>
              <ButtonLink href="#metrics" variant="ghost">
                Metric definitions
              </ButtonLink>
            </div>
          </div>
          <Panel variant="card" title="Overview · last 12 months" meta="Sample workspace">
            <KpiGrid
              kpis={overviewKpis("12m").slice(0, 4)}
              style={{ gridTemplateColumns: "repeat(2,minmax(0,1fr))" }}
            />
            <div className="cs-wide">
              <AreaChart
                points={mrrLine(stats)}
                width={560}
                height={200}
                labelEvery={1}
                zero
                label="Monthly recurring revenue"
              />
            </div>
          </Panel>
        </div>
      </section>

      <section className="section-sm bg-white">
        <div className="wrap">
          <IconCards cards={CAPABILITY_CARDS} />
        </div>
      </section>

      <section className="section-sm">
        <div className="wrap">
          <Feature
            style={{ paddingTop: 0 }}
            eyebrow="Segmentation"
            title="Compare the customers that grow with the ones that don't."
            lead="Put any two segments side by side and see where retention, ARPA and expansion diverge. It's the fastest way to find your best-fit customer."
            visual={
              <Panel
                variant="card"
                title="Net revenue retention by segment"
                meta="Trailing 12 months · axis 80–120%"
              >
                <SegmentBars />
                <p className="note">
                  Bars in amber are segments below 100% NRR, meaning they shrink without new sales.
                </p>
              </Panel>
            }
          >
            <CheckList items={SEGMENT_CHECKS} />
          </Feature>
          <Feature
            reverse
            eyebrow="Customer profiles"
            title="Every account's revenue story on one page."
            lead="Open any customer to see their MRR over time, every plan change, failed payment and note from your team, next to health signals from your CRM."
            visual={<CustomerProfile />}
          >
            <CheckList items={PROFILE_CHECKS} />
          </Feature>
        </div>
      </section>

      <section className="section-sm bg-white" id="cohorts">
        <div className="wrap">
          <SectionHead
            eyebrow="Cohorts"
            title="Retention curves by signup month."
            lead="Read across a row to follow one cohort over time, or down a column to see whether newer customers stick around longer than older ones."
          />
          <Panel
            variant="card"
            title="Net MRR retention"
            meta="Oct 2025 – Sep 2026 cohorts · darker = higher retention"
          >
            <div className="scroll-x">
              <CohortGrid cohorts={COHORTS} metric="net" />
            </div>
          </Panel>
        </div>
      </section>

      <section className="section-sm" id="forecast">
        <div className="wrap">
          <Feature
            style={{ padding: 0 }}
            eyebrow="Forecasting"
            title="Plan hiring against a range, not a hunch."
            lead="Forecasts start from your trailing growth, churn and expansion rates. Pick a scenario, override any assumption and share the result as a read-only link."
            visual={
              <Panel variant="card" title="MRR forecast · base scenario" meta="80% interval shaded">
                <div className="cs-wide">
                  <ForecastChart forecast={base} width={760} height={280} />
                </div>
              </Panel>
            }
          >
            <div className="stat-row">
              {forecasts.map((f) => (
                <div key={f.key}>
                  <small>{f.label}</small>
                  <b>{money(forecastEnd(f.forecast))}</b>
                </div>
              ))}
            </div>
            <p className="note">Projected MRR in September 2027 for the sample workspace.</p>
          </Feature>
        </div>
      </section>

      <section className="section-sm bg-white" id="metrics">
        <div className="wrap">
          <SectionHead
            eyebrow="Metric definitions"
            title="No black boxes. Every formula is documented."
            lead="These are the definitions Churnwise uses everywhere: dashboards, exports, the API and the weekly email."
          />
          <DefinitionsTable />
        </div>
      </section>

      <section className="section-sm">
        <div className="wrap">
          <IconCards cards={PLATFORM_CARDS} />
        </div>
      </section>

      <CtaBand />
    </>
  );
}
