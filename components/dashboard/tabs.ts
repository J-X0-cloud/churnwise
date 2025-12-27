import type { IconName } from "@/components/ui/icons";
import type { TabKey } from "@/types/revenue";

export const TABS: Array<{ key: TabKey; label: string; title: string; icon: IconName }> = [
  { key: "overview", label: "Overview", title: "Overview", icon: "overview" },
  { key: "revenue", label: "Revenue", title: "Revenue", icon: "revenue" },
  { key: "retention", label: "Retention", title: "Retention", icon: "retention" },
  { key: "customers", label: "Customers", title: "Customers", icon: "customers" },
  { key: "forecast", label: "Forecast", title: "Forecast", icon: "forecast" },
  { key: "recovery", label: "Recovery", title: "Payment recovery", icon: "recovery" },
];

export const isTabKey = (v: string): v is TabKey => TABS.some((t) => t.key === v);
