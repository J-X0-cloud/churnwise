import { BRAND, BRAND_DARK, MINT } from "@/lib/palette";

export interface PlanDefinition {
  name: string;
  price: string;
  color: string;
  /** Share of MRR at the start and end of the model. */
  mrrShare: [number, number];
  customerShare: [number, number];
  /** Monthly logo churn, % */
  churn: number;
}

export const PLANS: PlanDefinition[] = [
  {
    name: "Starter",
    price: "$99/mo",
    color: "#9ad8bd",
    mrrShare: [0.17, 0.12],
    customerShare: [0.46, 0.41],
    churn: 3.1,
  },
  {
    name: "Growth",
    price: "$349/mo",
    color: MINT,
    mrrShare: [0.38, 0.35],
    customerShare: [0.36, 0.37],
    churn: 1.6,
  },
  {
    name: "Scale",
    price: "$1,190/mo",
    color: BRAND,
    mrrShare: [0.29, 0.33],
    customerShare: [0.14, 0.16],
    churn: 0.9,
  },
  {
    name: "Enterprise",
    price: "Custom",
    color: BRAND_DARK,
    mrrShare: [0.16, 0.2],
    customerShare: [0.04, 0.06],
    churn: 0.4,
  },
];
