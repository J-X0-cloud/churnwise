"use client";

import { useTip } from "@/components/charts/TooltipProvider";
import { money, num } from "@/lib/format";
import type { PlanRow } from "@/types/revenue";

/** MRR share by plan as a single stacked bar, with a legend and an optional plan table. */
export function PlanMix({ plans, table = true }: { plans: PlanRow[]; table?: boolean }) {
  const tip = useTip();
  return (
    <>
      <div className="stackbar">
        {plans.map((p) => (
          <i
            key={p.name}
            style={{ width: `${p.share.toFixed(2)}%`, background: p.color }}
            {...tip(`${p.name}: ${money(p.mrr)} (${p.share.toFixed(1)}%)`)}
          />
        ))}
      </div>
      <div className="legend">
        {plans.map((p) => (
          <span key={p.name}>
            <i style={{ background: p.color }} />
            {p.name}
          </span>
        ))}
      </div>
      {table ? (
        <div className="scroll-x">
          <table className="tbl mini">
            <thead>
              <tr>
                <th>Plan</th>
                <th className="n">Customers</th>
                <th className="n">MRR</th>
                <th className="n">Churn</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((p) => (
                <tr key={p.name}>
                  <td>
                    <i className="dot" style={{ background: p.color }} />
                    {p.name} <small>{p.price}</small>
                  </td>
                  <td className="n">{num(p.customers)}</td>
                  <td className="n">{money(p.mrr)}</td>
                  <td className="n">{p.churn.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </>
  );
}
