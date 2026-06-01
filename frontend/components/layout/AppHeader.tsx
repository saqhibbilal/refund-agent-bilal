import type { HealthResponse } from "@/types/api";

import { AppNav } from "./AppNav";

interface AppHeaderProps {
  health?: HealthResponse | null;
  sessionId?: string | null;
}

function statusLabel(health: HealthResponse | null | undefined): {
  text: string;
  className: string;
} {
  if (!health) {
    return { text: "Connecting…", className: "bg-worknoon-ice/10 text-worknoon-ice/70" };
  }
  if (health.status === "ok") {
    return { text: "Ready", className: "bg-worknoon-ice text-worknoon-dark" };
  }
  if (health.status === "degraded") {
    return {
      text: "LLM not configured",
      className: "border border-worknoon-ice/25 bg-worknoon-ice/10 text-worknoon-ice",
    };
  }
  return { text: "Unavailable", className: "border border-worknoon-ice/35 bg-worknoon-dark text-worknoon-ice" };
}

export function AppHeader({ health, sessionId }: AppHeaderProps) {
  const status = statusLabel(health);

  return (
    <header className="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-worknoon-ice/15 bg-worknoon-dark/95 px-5 py-4 shadow-[0_1px_30px_rgba(214,239,255,0.08)] lg:px-6">
      <div>
        <h1 className="font-display text-xl font-semibold uppercase tracking-wide text-worknoon-ice lg:text-2xl">
          Worknoon Refund Agent
        </h1>
        <p className="mt-0.5 text-sm text-worknoon-ice/55">
          Agent reasoning · Customer chat
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <AppNav />
        {health !== undefined && (
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${status.className}`}
          >
            {status.text}
          </span>
        )}
        {sessionId && (
          <span className="hidden font-mono text-xs text-worknoon-ice/40 sm:inline">
            {sessionId.slice(0, 8)}…
          </span>
        )}
      </div>
    </header>
  );
}
