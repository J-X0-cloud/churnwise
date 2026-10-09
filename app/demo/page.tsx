import type { Metadata } from "next";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { DemoBar } from "@/components/dashboard/DemoBar";
import { getDashboard } from "@/lib/api";

export const metadata: Metadata = {
  title: "Live demo dashboard",
  description:
    "Interactive Churnwise demo: MRR, net revenue retention, cohorts, customers, forecasts and payment recovery for a sample SaaS workspace.",
};

// Rendered per request from the engine, which also means the build never needs the engine running.
export const dynamic = "force-dynamic";

export default async function DemoPage() {
  const data = await getDashboard();
  return (
    <div className="demo">
      <DemoBar />
      <DashboardShell data={data} />
    </div>
  );
}
