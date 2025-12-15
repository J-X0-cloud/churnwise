import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { TooltipProvider } from "@/components/charts/TooltipProvider";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://churnwise.com"),
  title: {
    default: "Churnwise | Subscription revenue analytics for SaaS",
    template: "%s | Churnwise",
  },
  description:
    "Churnwise turns your billing data into MRR, net revenue retention, churn, cohort and forecast reports, plus automated failed-payment recovery for SaaS teams.",
  icons: { icon: { url: "/favicon.svg", type: "image/svg+xml" } },
  openGraph: { siteName: "Churnwise", type: "website" },
};

export const viewport: Viewport = {
  themeColor: "#0b3d2e",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
