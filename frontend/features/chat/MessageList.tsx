import { useEffect, useRef } from "react";

import { DecisionTag } from "@/components/ui/DecisionTag";
import type { ChatMessage } from "@/types/api";

import { MessageContent } from "./MessageContent";

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="scroll-area flex-1 space-y-4 overflow-y-auto px-4 py-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[85%] rounded-xl px-4 py-3 text-chat leading-relaxed ${
              message.role === "user"
                ? "bg-worknoon-ice text-worknoon-dark shadow-[0_10px_30px_rgba(214,239,255,0.12)]"
                : "border border-worknoon-ice/15 bg-worknoon-panel text-worknoon-ice"
            }`}
          >
            {message.role === "assistant" ? (
              <>
                <MessageDecisionTag content={message.content} />
                <MessageContent
                  content={message.content}
                  isStreaming={message.isStreaming}
                />
              </>
            ) : (
              <p className="whitespace-pre-wrap">
                {message.content}
                {message.isStreaming && (
                  <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-worknoon-dark/40" />
                )}
              </p>
            )}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function MessageDecisionTag({ content }: { content: string }) {
  const normalized = content.toLowerCase();
  if (normalized.includes("escalated to human review")) {
    return <DecisionTag action="escalate" className="mb-3" />;
  }
  if (normalized.includes("approved")) {
    return <DecisionTag action="approve" className="mb-3" />;
  }
  if (normalized.includes("denied")) {
    return <DecisionTag action="deny" className="mb-3" />;
  }
  return null;
}
