import type { ChatSessionState } from "@/hooks/useChatSession";

import { TraceTimeline } from "./TraceTimeline";

type AdminTracePanelProps = Pick<
  ChatSessionState,
  "traceEvents" | "isLoading" | "sessionId"
>;

export function AdminTracePanel({
  traceEvents,
  isLoading,
  sessionId,
}: AdminTracePanelProps) {
  return (
    <div className="flex h-full flex-col bg-worknoon-dark/95">
      <div className="shrink-0 border-b border-worknoon-ice/15 bg-worknoon-dark/95 px-4 py-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-worknoon-ice/55">
          Agent Reasoning
        </h2>
        <p className="mt-0.5 text-xs text-worknoon-ice/45">
          Live tool calls and policy validation
          {sessionId ? ` · session ${sessionId.slice(0, 8)}` : ""}
        </p>
      </div>
      <TraceTimeline events={traceEvents} isLoading={isLoading} />
    </div>
  );
}
