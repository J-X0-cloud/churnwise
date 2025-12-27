import clsx from "clsx";

import { ButtonLink } from "@/components/ui/ButtonLink";
import { PLANS, planCta } from "@/lib/data/pricing";

export function PricingPlans() {
  return (
    <div className="plans">
      {PLANS.map((plan) => {
        const cta = planCta(plan);
        const [heading, ...items] = plan.features;
        return (
          <div key={plan.name} className={clsx("plan", plan.popular && "pop")}>
            {plan.popular ? <span className="badge">Most popular</span> : null}
            <h3>{plan.name}</h3>
            <p className="for">{plan.audience}</p>
            <div className="price">
              {plan.price}
              {plan.price === "Custom" ? null : <small>/mo</small>}
            </div>
            <div className="cap">{plan.cap}</div>
            <ButtonLink href={cta.href} variant={plan.popular ? "primary" : "ghost"}>
              {cta.label}
            </ButtonLink>
            <ul>
              <li className="h">{heading}</li>
              {items.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
