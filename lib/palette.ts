import type { Movement } from "@/types/revenue";

/** Movement palette, checked for colour-blind separation on a light surface. */
export const MOVEMENT_COLORS: Record<Movement, string> = {
  new: "#0f7a56",
  expansion: "#3cc28f",
  reactivation: "#3a73d6",
  contraction: "#eda100",
  churn: "#d9463e",
};

export const MOVEMENTS: Array<{ key: Movement; label: string; short: string; color: string; sign: 1 | -1 }> =
  [
    { key: "new", label: "New", short: "New", color: MOVEMENT_COLORS.new, sign: 1 },
    { key: "expansion", label: "Expansion", short: "Expansion", color: MOVEMENT_COLORS.expansion, sign: 1 },
    {
      key: "reactivation",
      label: "Reactivation",
      short: "Reactiv.",
      color: MOVEMENT_COLORS.reactivation,
      sign: 1,
    },
    {
      key: "contraction",
      label: "Contraction",
      short: "Contract.",
      color: MOVEMENT_COLORS.contraction,
      sign: -1,
    },
    { key: "churn", label: "Churn", short: "Churn", color: MOVEMENT_COLORS.churn, sign: -1 },
  ];

export const BRAND = "#0f7a56";
export const BRAND_DARK = "#0b3d2e";
export const INK = "#0d1f1a";
export const MUTED = "#5b6b66";

export const { expansion: MINT, reactivation: BLUE, contraction: AMBER, churn: RED } = MOVEMENT_COLORS;
