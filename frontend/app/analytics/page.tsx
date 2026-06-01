import { AnalyticsHeader } from "@/components/layout/AnalyticsHeader";
import { AnalyticsDashboard } from "@/features/analytics/AnalyticsDashboard";

export default function AnalyticsPage() {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-worknoon-dark">
      <AnalyticsHeader />
      <AnalyticsDashboard />
    </div>
  );
}
