import { Legend } from "@/components/charts/Legend";
import { INK, MOVEMENTS } from "@/lib/palette";

export function MovementLegend({ net = true }: { net?: boolean }) {
  return (
    <Legend
      items={[
        ...MOVEMENTS.map((m) => ({ label: m.label, color: m.color })),
        ...(net ? [{ label: "Net new MRR", color: INK, kind: "line" as const }] : []),
      ]}
    />
  );
}
