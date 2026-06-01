"use client";

import { useState } from "react";

import { DecisionTag } from "@/components/ui/DecisionTag";
import type { RefundOutcome, TraceEventItem } from "@/types/api";

interface TraceEventRowProps {
  event: TraceEventItem;
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function isDecisionAction(
  action: unknown,
): action is RefundOutcome["action"] {
  return action === "approve" || action === "deny" || action === "escalate";
}

function eventStyles(type: string): string {
  if (type === "injection_warning") {
    return "border-worknoon-ice/25 bg-worknoon-ice/[0.045]";
  }
  if (type === "decision") {
    return "border-worknoon-ice/20 bg-worknoon-ice/[0.035]";
  }
  if (type === "tool_start" || type === "tool_end") {
    return "border-worknoon-ice/15 bg-worknoon-dark/80";
  }
  return "border-worknoon-ice/15 bg-worknoon-dark/75";
}

export function TraceEventRow({ event }: TraceEventRowProps) {
  const [expanded, setExpanded] = useState(false);
  const hasDetails = Object.keys(event.payload).length > 0;
  const decisionAction = isDecisionAction(event.payload.action)
    ? event.payload.action
    : null;

  return (
    <div className={`overflow-hidden rounded-lg border px-3 py-2.5 ${eventStyles(event.type)}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs font-semibold uppercase text-worknoon-ice/65">
            {event.type}
          </span>
          {event.type === "decision" && decisionAction && (
            <DecisionTag action={decisionAction} />
          )}
          <span className="text-xs text-worknoon-ice/40">{formatTime(event.timestamp)}</span>
        </div>
        {hasDetails && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="text-xs font-medium text-worknoon-ice/70 hover:text-worknoon-ice"
          >
            {expanded ? "Hide" : "Details"}
          </button>
        )}
      </div>

      {event.type === "tool_start" && (
        <p className="mt-1.5 text-sm text-worknoon-ice/75">
          Tool: <code className="break-words font-mono text-xs text-worknoon-ice/90">{String(event.payload.tool)}</code>
        </p>
      )}

      {event.type === "tool_end" && (
        <p className="mt-1.5 text-sm text-worknoon-ice/75">
          Completed:{" "}
          <code className="break-words font-mono text-xs text-worknoon-ice/90">{String(event.payload.tool)}</code>
        </p>
      )}

      {event.type === "injection_warning" && (
        <p className="mt-1.5 break-words text-sm text-worknoon-ice/90">
          {String(event.payload.message ?? "Injection pattern detected")}
        </p>
      )}

      {event.type === "decision" && !decisionAction && (
        <p className="mt-1.5 text-sm text-worknoon-ice/75">
          Order {String(event.payload.order_id)}
        </p>
      )}

      {event.type === "decision" && decisionAction && (
        <p className="mt-1.5 text-sm text-worknoon-ice/60">
          Order {String(event.payload.order_id)}
        </p>
      )}

      {expanded && hasDetails && (
        <pre className="scroll-area mt-2 max-h-48 overflow-auto rounded border border-worknoon-ice/15 bg-worknoon-dark/70 p-2 font-mono text-xs text-worknoon-ice/80">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      )}
    </div>
  );
}
