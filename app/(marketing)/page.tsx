import Link from "next/link";

import { ForecastChart } from "@/components/charts/ForecastChart";
import { Legend } from "@/components/charts/Legend";
import { MovementChart } from "@/components/charts/MovementChart";
import { OutcomeFunnel } from "@/components/charts/OutcomeFunnel";
import { Waterfall } from "@/components/charts/Waterfall";
import { AppWindow } from "@/components/dashboard/AppWindow";
import { CohortGrid } from "@/components/dashboard/CohortGrid";
import { MovementLegend } from "@/components/dashboard/MovementLegend";
import { Panel } from "@/components/dashboard/Panel";
import { CtaBand } from "@/components/marketing/CtaBand";
import { Feature } from "@/components/marketing/Feature";
import { Integrations } from "@/components/marketing/Integrations";
import { MetricStrip } from "@/components/marketing/MetricStrip";
import { Roles } from "@/components/marketing/Roles";
import { SectionHead } from "@/components/marketing/SectionHead";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { CheckList } from "@/components/ui/CheckList";
import { COHORTS } from "@/lib/data/cohorts";
import { FEATURE_CHECKS, HERO_CONNECTORS } from "@/lib/data/home";
import { TRIAL_URL } from "@/lib/data/site";
import { forecast, forecastEnd } from "@/lib/forecast";
import { money } from "@/lib/format";
import { BRAND, INK } from "@/lib/palette";
import { recoveryFunnel } from "@/lib/recovery";
import { movementBuckets, rangeStats, sumTotals } from "@/lib/revenue";

export default function HomePage() {
  const buckets = movementBuckets("12m");
  const totals = sumTotals(buckets);
  const stats = rangeStats("12m");
  const base = forecast("base");
  const funnel = recoveryFunnel();

  return (
    <>
      <section className="hero">
        <div className="wrap">
          <div className="hero-copy">
            <div>
              <span className="eyebrow">Subscription revenue analytics</span>
              <h1>
                Know where your recurring revenue <em>comes from</em> and where it leaks.
              </h1>
            </div>
            <div>
              <p className="lead">
                Churnwise reads your billing data and turns every invoice, upgrade, downgrade and failed
                charge into MRR, retention, cohort and forecast reports your whole team can trust. No
                spreadsheets, no SQL, no month-end reconciling.
              </p>
              <div className="hero-cta">
                <ButtonLink href="/demo" arrow>
                  Explore the live demo
                </ButtonLink>
                <ButtonLink href={TRIAL_URL} variant="ghost">
                  Start a 14-day trial
                </ButtonLink>
              </div>
              <div className="connects">
                <span>Read-only connections to</span>
                {HERO_CONNECTORS.map((c) => (
                  <b key={c}>{c}</b>
                ))}
                <span>and more</span>
              </div>
            </div>
          </div>
          <div className="hero-shot">
            <AppWindow />
          </div>
        </div>
      </section>

      <section className="section-sm">
        <div className="wrap">
          <SectionHead
            eyebrow="One set of definitions"
            title="The numbers your board deck, your finance team and your CS team all agree on."
          />
          <MetricStrip />
        </div>
      </section>

      <section className="section-sm bg-white" id="features">
        <div className="wrap">
          <Feature
            eyebrow="MRR movements"
            title="Every dollar of change, explained."
            lead="See exactly how you got from last month's MRR to this month's: new business, expansion, reactivations, downgrades and churn, each one traceable to the customer and the invoice behind it."
            visual={
              <Panel
                variant="card"
                title="MRR bridge"
                meta="Oct 2025 – Sep 2026"
                aside={<span className="r pill g">+{money(stats.netNew)} net new</span>}
              >
                <Waterfall start={stats.mrrStart} totals={totals} end={stats.mrr} width={620} height={300} />
                <div className="ph" style={{ marginTop: 18 }}>
                  <h4>Monthly movements</h4>
                </div>
                <div className="cs-wide">
                  <MovementChart buckets={buckets} width={620} height={230} />
                </div>
                <MovementLegend />
              </Panel>
            }
          >
            <CheckList items={FEATURE_CHECKS.movements} />
            <Link className="tlink" href="/product">
              How revenue analytics works &rarr;
            </Link>
          </Feature>

          <Feature
            id="cohorts"
            reverse
            eyebrow="Cohorts & retention"
            title="Spot the cohort that's quietly slipping."
            lead="Monthly cohorts by revenue or by logo, with expansion baked in. Compare the customers you signed after a pricing change with the ones before it, side by side."
            visual={
              <Panel variant="card" title="Net MRR retention by signup month" meta="% of starting MRR">
                <div className="scroll-x">
                  <CohortGrid cohorts={COHORTS} metric="net" months={9} rows={9} compact />
                </div>
              </Panel>
            }
          >
            <CheckList items={FEATURE_CHECKS.cohorts} />
          </Feature>

          <Feature
            id="forecast"
            eyebrow="Forecasting"
            title="A forecast built from how your customers actually behave."
            lead="Churnwise projects MRR from your real new-business pace, expansion and churn curves, then shows the range, not just a single line. Adjust the assumptions and watch the band move."
            visual={
              <Panel
                variant="card"
                title="MRR forecast"
                meta="Base scenario, next 12 months"
                aside={<span className="r pill g">{money(forecastEnd(base))} by Sep 2027</span>}
              >
                <div className="cs-wide">
                  <ForecastChart forecast={base} width={640} height={270} />
                </div>
                <Legend
                  items={[
                    { label: "Actual", color: INK, kind: "line" },
                    { label: "Forecast", color: BRAND, kind: "line" },
                    { label: "80% interval", color: BRAND, kind: "band" },
                  ]}
                />
              </Panel>
            }
          >
            <CheckList items={FEATURE_CHECKS.forecast} />
          </Feature>

          <Feature
            reverse
            eyebrow="Payment recovery"
            title="Win back the customers who never meant to leave."
            lead="Failed payments cause a big share of SaaS churn. Churnwise retries at the times cards are most likely to succeed, sends friendly branded reminders and gives customers a one-click card update page."
            visual={
              <Panel
                variant="card"
                title="Failed payments, last 12 months"
                aside={<span className="r pill g">{funnel.rate.toFixed(0)}% recovered</span>}
              >
                <OutcomeFunnel items={funnel.items} />
              </Panel>
            }
          >
            <CheckList items={FEATURE_CHECKS.recovery} />
            <Link className="tlink" href="/recovery">
              Explore payment recovery &rarr;
            </Link>
          </Feature>
        </div>
      </section>

      <Roles />

      <section className="section">
        <div className="wrap">
          <SectionHead
            centered
            eyebrow="Connections"
            title="Plug in the billing stack you already run."
            lead="Read-only access, full history backfilled in minutes, and multiple sources merged into one customer record."
          />
          <Integrations />
        </div>
      </section>

      <CtaBand />
    </>
  );
}
