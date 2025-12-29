import type { Metadata } from "next";

import { BarChart } from "@/components/charts/BarChart";
import { HBarList } from "@/components/charts/HBarList";
import { OutcomeFunnel } from "@/components/charts/OutcomeFunnel";
import { OpenFailedTable } from "@/components/dashboard/OpenFailedTable";
import { Panel } from "@/components/dashboard/Panel";
import { CardUpdatePreview } from "@/components/marketing/CardUpdatePreview";
import { CtaBand } from "@/components/marketing/CtaBand";
import { Faq } from "@/components/marketing/Faq";
import { Feature } from "@/components/marketing/Feature";
import { ReminderSequence } from "@/components/marketing/ReminderSequence";
import { RetryTimeline } from "@/components/marketing/RetryTimeline";
import { SectionHead } from "@/components/marketing/SectionHead";
import { ButtonLink } from "@/components/ui/ButtonLink";
import { CheckList } from "@/components/ui/CheckList";
import { DECLINE_REASONS, RECOVERY_CHECKS, RECOVERY_FAQ } from "@/lib/data/recovery";
import { TRIAL_URL } from "@/lib/data/site";
import { money } from "@/lib/format";
import { BRAND, MINT } from "@/lib/palette";
import { recoveryByMonth, recoveryFunnel } from "@/lib/recovery";

export const metadata: Metadata = {
  title: "Failed payment recovery & dunning",
  description:
    "Smart retries, branded reminder emails, in-app banners and a hosted card-update page that recover failed subscription payments, with reporting built in.",
};

export default function RecoveryPage() {
  const funnel = recoveryFunnel();
  const months = recoveryByMonth(12);

  return (
    <>
      <section className="phero">
        <div className="wrap split">
          <div>
            <span className="eyebrow">Payment recovery</span>
            <h1 style={{ fontSize: "clamp(36px,4.6vw,58px)" }}>Stop losing customers to expired cards.</h1>
            <p className="lead">
              A declined charge isn&apos;t a cancellation. Churnwise retries at the right moment, reminds
              customers politely and makes updating a card take ten seconds, then shows you exactly how much
              revenue it brought back.
            </p>
            <div className="hero-cta">
              <ButtonLink href={TRIAL_URL} arrow>
                Turn on recovery
              </ButtonLink>
              <ButtonLink href="/demo#recovery" variant="ghost">
                See it in the demo
              </ButtonLink>
            </div>
          </div>
          <Panel
            variant="card"
            title="Failed payments · last 12 months"
            aside={<span className="r pill g">{money(funnel.recovered)} recovered</span>}
          >
            <OutcomeFunnel items={funnel.items} />
          </Panel>
        </div>
      </section>

      <section className="section-sm bg-white">
        <div className="wrap">
          <SectionHead
            eyebrow="Smart retries"
            title="Retries timed to the decline, not the calendar."
            lead={`An "insufficient funds" decline gets retried after payday. An expired card skips retries entirely and goes straight to a card-update request. Each step is logged on the customer's timeline.`}
          />
          <RetryTimeline />
        </div>
      </section>

      <section className="section-sm">
        <div className="wrap">
          <Feature
            style={{ paddingTop: 0 }}
            eyebrow="Reminder sequences"
            title="Emails that sound like you."
            lead="Write the sequence once in your own voice and branding. Churnwise stops it the moment the payment goes through, so nobody gets a reminder after they've paid."
            visual={<ReminderSequence />}
          >
            <CheckList items={RECOVERY_CHECKS} />
          </Feature>
          <Feature
            reverse
            eyebrow="In-app & card update"
            title="Meet customers where they already are."
            lead="Drop in a small script to show a payment banner to account admins, or a gentle paywall after the grace period. The hosted card-update page carries your logo and colors."
            visual={<CardUpdatePreview />}
          />
        </div>
      </section>

      <section className="section-sm bg-white">
        <div className="wrap">
          <SectionHead eyebrow="Recovery reporting" title="See what recovery is worth, every month." />
          <div className="grid-2">
            <Panel variant="card" title="Recovered revenue by month" meta="Oct 2025 – Sep 2026">
              <div className="cs-wide">
                <BarChart
                  data={months.map((m) => ({ label: m.label, value: m.recovered }))}
                  width={620}
                  height={220}
                  color={MINT}
                  label="Recovered revenue by month"
                />
              </div>
            </Panel>
            <Panel variant="card" title="Why charges fail" meta="Share of declines">
              <HBarList items={DECLINE_REASONS} color={BRAND} />
            </Panel>
          </div>
          <Panel
            variant="card"
            title="Open failed payments"
            meta="In recovery right now"
            style={{ marginTop: 18 }}
          >
            <div className="scroll-x">
              <OpenFailedTable />
            </div>
          </Panel>
        </div>
      </section>

      <section className="section-sm">
        <div className="wrap">
          <Faq title="Payment recovery questions" items={RECOVERY_FAQ} />
        </div>
      </section>

      <CtaBand
        title="Recover revenue you've already earned."
        body="Recovery runs on top of Churnwise analytics, so every dollar it saves shows up in your churn numbers."
      />
    </>
  );
}
