import { NextResponse } from "next/server";
import { z } from "zod";

import { RANGE_KEYS, movementBuckets, quickRatio, rangeStats, sumTotals } from "@/lib/revenue";
import type { RangeKey } from "@/types/revenue";

const QuerySchema = z.object({
  range: z.enum(RANGE_KEYS as [RangeKey, ...RangeKey[]]).default("12m"),
  movements: z.stringbool().default(false),
});

/**
 * GET /api/metrics?range=12m&movements=true — headline revenue metrics for the workspace, the same
 * numbers the dashboard tiles show. Optionally includes per-period MRR movements.
 */
export function GET(request: Request) {
  const params = Object.fromEntries(new URL(request.url).searchParams);
  const parsed = QuerySchema.safeParse(params);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "invalid_query", issues: z.flattenError(parsed.error).fieldErrors },
      { status: 400 },
    );
  }

  const { range, movements } = parsed.data;
  const { line, ...stats } = rangeStats(range);
  const buckets = movementBuckets(range);

  return NextResponse.json({
    range,
    metrics: {
      ...stats,
      quickRatio: quickRatio(sumTotals(buckets)),
    },
    mrrSeries: line.map((p) => ({
      date: p.date.toISOString().slice(0, 10),
      mrr: Math.round(p.value * 100) / 100,
    })),
    ...(movements
      ? {
          movements: buckets.map((b) => ({
            period: b.label,
            new: b.new,
            expansion: b.expansion,
            reactivation: b.reactivation,
            contraction: b.contraction,
            churn: b.churn,
            net: b.net,
          })),
        }
      : {}),
  });
}
