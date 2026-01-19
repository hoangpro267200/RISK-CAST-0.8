export type TabType = "overview" | "transport" | "cargo" | "analytics";
export type StatusType = "good" | "medium" | "high" | "low" | "neutral";

export interface KPIMetric {
  label: string;
  value: string;
  unit?: string;
  status: StatusType;
  trend?: string;
  subtext: string;
}





