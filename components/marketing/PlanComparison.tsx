import { Fragment } from "react";

import { COMPARISON, PLANS } from "@/lib/data/pricing";
import type { Cell } from "@/lib/data/pricing";

function Value({ cell }: { cell: Cell }) {
  if (cell === true) return <span className="y">✓</span>;
  if (cell === false) return <span className="no">&mdash;</span>;
  return <>{cell}</>;
}

export function PlanComparison() {
  return (
    <div className="scroll-x">
      <table className="cmp">
        <thead>
          <tr>
            <th>Feature</th>
            {PLANS.map((p) => (
              <th key={p.name}>{p.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {COMPARISON.map((group) => (
            <Fragment key={group.group}>
              <tr className="grp">
                <td colSpan={5}>{group.group}</td>
              </tr>
              {group.rows.map(([feature, cells]) => (
                <tr key={feature}>
                  <td>{feature}</td>
                  {cells.map((c, i) => (
                    <td key={i}>
                      <Value cell={c} />
                    </td>
                  ))}
                </tr>
              ))}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
