import type { Metadata } from "next";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { DemoBar } from "@/components/dashboard/DemoBar";

export const metadata: Metadata = {
  title: "Live demo dashboard",
  description:
    "Interactive Churnwise demo: MRR, net revenue retention, cohorts, customers, forecasts and payment recovery for a sample SaaS workspace.",
};

export default function DemoPage() {
  return (
    <div className="demo">
      <DemoBar />
      <DashboardShell />
    </div>
  );
}
