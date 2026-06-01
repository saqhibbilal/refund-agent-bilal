import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import type { ChatSessionState } from "@/hooks/useChatSession";

import { ChatInput } from "./ChatInput";
import {
  DEMO_SCENARIOS,
  QUICK_HELP_SUGGESTIONS,
  getFollowUpSuggestions,
} from "./demoSuggestions";
import { MessageList } from "./MessageList";
import { SuggestionPanel } from "./SuggestionPanel";

type CustomerChatPanelProps = Pick<
  ChatSessionState,
  | "messages"
  | "outcome"
  | "isLoading"
  | "isInitializing"
  | "error"
  | "sendMessage"
  | "resetConversation"
  | "clearError"
>;

export function CustomerChatPanel({
  messages,
  outcome,
  isLoading,
  isInitializing,
  error,
  sendMessage,
  resetConversation,
  clearError,
}: CustomerChatPanelProps) {
  const hasUserMessage = messages.some((message) => message.role === "user");
  const starterSuggestions = [...QUICK_HELP_SUGGESTIONS, ...DEMO_SCENARIOS];
  const followUpSuggestions = getFollowUpSuggestions(messages, outcome);
  const controlsDisabled = isLoading || isInitializing;

  return (
    <div className="flex h-full flex-col bg-worknoon-dark/95">
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-worknoon-ice/15 px-4 py-3">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[#D6EFFF]" style={{ fontSize: "1.1em" }}>
            Customer Chat
          </h2>
     
          <p className="mt-1 text-xs text-worknoon-ice/40">
            Guided refund support with ready-to-try demo cases
          </p>
        </div>
        <div className="flex min-w-0 flex-wrap items-center justify-end gap-3">
          <span className="hidden text-right text-xs text-worknoon-ice/40 sm:inline">
            For more guided prompts, start a new conversation.
          </span>
          <button
            type="button"
            onClick={resetConversation}
            disabled={controlsDisabled}
            className="rounded-full border border-worknoon-ice/15 px-3 py-1.5 text-xs font-semibold text-worknoon-ice/75 transition hover:border-worknoon-ice/35 hover:bg-worknoon-ice/[0.06] disabled:cursor-not-allowed disabled:opacity-40"
          >
            New conversation
          </button>
        </div>
      </div>

      {error && (
        <div className="mx-4 mt-3 flex items-start justify-between gap-2 rounded-lg border border-worknoon-ice/35 bg-worknoon-ice/10 px-3 py-2 text-sm text-worknoon-ice">
          <span>{error}</span>
          <button
            type="button"
            onClick={clearError}
            className="shrink-0 text-xs font-medium underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {isInitializing ? (
        <div className="flex flex-1 items-center justify-center">
          <LoadingSpinner label="Starting session…" />
        </div>
      ) : (
        <>
          {!hasUserMessage && (
            <SuggestionPanel
              title="Start with a guided prompt"
              subtitle="Pick a case; the logged-in profile and order context are already included."
              suggestions={starterSuggestions}
              onSelect={sendMessage}
              disabled={controlsDisabled}
              variant="cards"
            />
          )}
          <MessageList messages={messages} />
          {hasUserMessage && (
            <SuggestionPanel
              title="Suggested follow-ups"
              suggestions={followUpSuggestions}
              onSelect={sendMessage}
              disabled={controlsDisabled}
            />
          )}
          <ChatInput onSend={sendMessage} disabled={isLoading || isInitializing} />
        </>
      )}
    </div>
  );
}
