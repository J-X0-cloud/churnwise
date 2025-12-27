import clsx from "clsx";
import type { CSSProperties } from "react";

import { Sparkline } from "@/components/charts/Sparkline";
import type { Kpi } from "@/types/revenue";

import { DeltaBadge } from "./DeltaBadge";

export function KpiTile({ kpi, spark = true }: { kpi: Kpi; spark?: boolean }) {
  return (
    <div className="kpi">
      <div className="kpi-l">
        {kpi.label}
        {kpi.hint ? <abbr title={kpi.hint}>i</abbr> : null}
      </div>
      <div className="kpi-v">
        {kpi.value}
        {kpi.unit ? <small>{kpi.unit}</small> : null}
      </div>
      <div className="kpi-f">
        <DeltaBadge delta={kpi.delta} />
        {spark && kpi.spark ? (
          <Sparkline values={kpi.spark} width={80} height={24} color={kpi.sparkColor} />
        ) : null}
      </div>
    </div>
  );
}

interface KpiGridProps {
  kpis: Kpi[];
  columns?: 4;
  spark?: boolean;
  style?: CSSProperties;
}

export function KpiGrid({ kpis, columns, spark = true, style }: KpiGridProps) {
  return (
    <div className={clsx("kpis", columns === 4 && "k4")} style={style}>
      {kpis.map((k) => (
        <KpiTile key={k.label} kpi={k} spark={spark} />
      ))}
    </div>
  );
}
