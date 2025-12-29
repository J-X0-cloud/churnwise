import type { Metadata } from "next";

import { AddOns } from "@/components/marketing/AddOns";
import { CtaBand } from "@/components/marketing/CtaBand";
import { Faq } from "@/components/marketing/Faq";
import { PlanComparison } from "@/components/marketing/PlanComparison";
import { PricingPlans } from "@/components/marketing/PricingPlans";
import { SectionHead } from "@/components/marketing/SectionHead";
import { PRICING_FAQ } from "@/lib/data/pricing";

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Churnwise plans from $79/month, priced by tracked MRR, with payment recovery and cancellation insights add-ons. 14-day free trial on every plan.",
};

export default function PricingPage() {
  return (
    <>
      <section className="phero" style={{ paddingBottom: 40 }}>
        <div className="wrap" style={{ textAlign: "center" }}>
          <span className="eyebrow">Pricing</span>
          <h1 style={{ fontSize: "clamp(36px,4.6vw,58px)", maxWidth: 900, margin: "0 auto .4em" }}>
            Priced by the revenue you track, not by the seat.
          </h1>
          <p className="lead" style={{ margin: "0 auto" }}>
            Every plan starts with a 14-day free trial and your full billing history. Pay annually and get two
            months free.
          </p>
          <div className="bill">
            <span className="pill g">Annual billing saves 2 months</span>
            <span>Prices shown billed monthly, in USD</span>
          </div>
        </div>
      </section>

      <section style={{ paddingBottom: 72 }}>
        <div className="wrap">
          <PricingPlans />
        </div>
      </section>

      <section className="section-sm bg-white">
        <div className="wrap">
          <SectionHead eyebrow="Add-ons" title="Add recovery and cancellation insights to any plan." />
          <AddOns />
        </div>
      </section>

      <section className="section-sm">
        <div className="wrap">
          <SectionHead centered title="Compare plans" />
          <PlanComparison />
        </div>
      </section>

      <section className="section-sm bg-white">
        <div className="wrap">
          <Faq title="Frequently asked questions" items={PRICING_FAQ} />
        </div>
      </section>

      <CtaBand
        title="Try every feature free for 14 days."
        body="Connect a billing system and see your real numbers before you pay anything."
      />
    </>
  );
}
