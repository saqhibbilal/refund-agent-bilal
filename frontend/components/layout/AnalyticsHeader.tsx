import { AppNav } from "./AppNav";

export function AnalyticsHeader() {
  return (
    <header className="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-worknoon-ice/15 bg-worknoon-dark/95 px-5 py-4 shadow-[0_1px_30px_rgba(214,239,255,0.08)] lg:px-6">
      <div>
        <h1 className="font-display text-xl font-semibold uppercase tracking-wide text-worknoon-ice lg:text-2xl">
          Worknoon Refund Agent
        </h1>
        <p className="mt-0.5 text-sm text-worknoon-ice/55">
          Business overview · Customer & refund insights
        </p>
      </div>
      <AppNav />
    </header>
  );
}
