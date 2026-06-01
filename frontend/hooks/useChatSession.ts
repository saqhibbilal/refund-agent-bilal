"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { createSession, fetchHealth, sendMessageStream } from "@/lib/api-client";
import { recordScenarioDecision } from "@/lib/scenarioDecisions";
import { readSSEStream } from "@/lib/sse";
import type {
  AgentRecommendation,
  ChatMessage,
  HealthResponse,
  RefundOutcome,
  TraceEventItem,
} from "@/types/api";

function newId(): string {
  return crypto.randomUUID();
}

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Welcome to Worknoon Support. I can help check refund options, explain policy rules, and guide you through the next step. Choose a sample scenario below or ask your own question.",
};

export function useChatSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [traceEvents, setTraceEvents] = useState<TraceEventItem[]>([]);
  const [outcome, setOutcome] = useState<RefundOutcome | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const traceIdRef = useRef(0);

  const appendTrace = useCallback((type: string, payload: Record<string, unknown>) => {
    traceIdRef.current += 1;
    const item: TraceEventItem = {
      id: `trace-${traceIdRef.current}`,
      type,
      payload,
      timestamp: Date.now(),
    };
    setTraceEvents((prev) => [...prev, item]);
  }, []);

  const resetConversation = useCallback(async () => {
    setIsInitializing(true);
    setError(null);
    setOutcome(null);
    setTraceEvents([]);
    traceIdRef.current = 0;

    try {
      const sessionRes = await createSession();
      setSessionId(sessionRes.session_id);
      setMessages([{ ...WELCOME_MESSAGE }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start session");
    } finally {
      setIsInitializing(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const [healthRes, sessionRes] = await Promise.all([
          fetchHealth().catch(() => null),
          createSession(),
        ]);
        if (cancelled) return;
        setHealth(healthRes);
        setSessionId(sessionRes.session_id);
        setMessages([{ ...WELCOME_MESSAGE }]);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to start session");
        }
      } finally {
        if (!cancelled) setIsInitializing(false);
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!sessionId || !content.trim() || isLoading) return;

      setError(null);
      setOutcome(null);
      setIsLoading(true);

      const userMessageId = newId();
      const assistantMessageId = newId();
      const clientMessageId = newId();

      setMessages((prev) => [
        ...prev,
        { id: userMessageId, role: "user", content: content.trim() },
        { id: assistantMessageId, role: "assistant", content: "", isStreaming: true },
      ]);

      let streamedText = "";

      try {
        const response = await sendMessageStream(
          sessionId,
          content.trim(),
          clientMessageId,
        );

        for await (const { event, data } of readSSEStream(response.body!)) {
          switch (event) {
            case "token": {
              const text = String(data.text ?? "");
              streamedText += text;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: streamedText, isStreaming: true }
                    : msg,
                ),
              );
              break;
            }
            case "tool_start":
            case "tool_end":
            case "injection_warning":
            case "validation":
              appendTrace(event, data);
              break;
            case "decision": {
              appendTrace("decision", data);
              const rec = data as unknown as AgentRecommendation;
              setOutcome({
                action: rec.action,
                order_id: rec.order_id,
                amount_cents: rec.amount_cents,
                reason: rec.reason,
                rule_ids: rec.rule_ids ?? [],
              });
              recordScenarioDecision(rec);
              break;
            }
            case "done": {
              const finalText = String(data.response_text ?? streamedText);
              streamedText = finalText;
              const rec = data.recommendation as AgentRecommendation | null;
              if (rec) {
                setOutcome({
                  action: rec.action,
                  order_id: rec.order_id,
                  amount_cents: rec.amount_cents,
                  reason: rec.reason,
                  rule_ids: rec.rule_ids ?? [],
                });
                recordScenarioDecision(rec);
              }
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: finalText, isStreaming: false }
                    : msg,
                ),
              );
              break;
            }
            case "error": {
              const msg = String(data.message ?? "Agent error");
              throw new Error(msg);
            }
            default:
              appendTrace(event, data);
          }
        }

        if (!streamedText) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: "I could not complete your request. Please try again.",
                    isStreaming: false,
                  }
                : msg,
            ),
          );
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Message failed";
        setError(message);
        setMessages((prev) =>
          prev.filter((msg) => msg.id !== assistantMessageId).concat(
            {
              id: assistantMessageId,
              role: "assistant",
              content: `Sorry, something went wrong: ${message}`,
              isStreaming: false,
            },
          ),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading, appendTrace],
  );

  return {
    sessionId,
    messages,
    traceEvents,
    outcome,
    isLoading,
    isInitializing,
    error,
    health,
    sendMessage,
    resetConversation,
    clearError: () => setError(null),
  };
}

export type ChatSessionState = ReturnType<typeof useChatSession>;
