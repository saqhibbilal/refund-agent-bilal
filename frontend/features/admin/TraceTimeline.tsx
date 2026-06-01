import { useEffect, useRef } from "react";

import type { TraceEventItem } from "@/types/api";

import { TraceEventRow } from "./TraceEventRow";

interface TraceTimelineProps {
  events: TraceEventItem[];
  isLoading: boolean;
}

export function TraceTimeline({ events, isLoading }: TraceTimelineProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events, isLoading]);

  return (
    <div className="scroll-area flex-1 space-y-2 overflow-y-auto px-4 py-4">
      {events.length === 0 && !isLoading && (
        <p className="text-center text-sm text-worknoon-ice/45">
          Agent reasoning will appear here when you send a message.
        </p>
      )}
      {events.map((event) => (
        <TraceEventRow key={event.id} event={event} />
      ))}
      {isLoading && (
        <div className="flex items-center gap-3 rounded-lg border border-dashed border-worknoon-ice/25 bg-worknoon-ice/5 px-4 py-3">
          <div
            className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-worknoon-ice/20 border-t-worknoon-ice"
            aria-hidden
          />
          <span className="text-sm text-worknoon-ice/70">Agent is working…</span>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
