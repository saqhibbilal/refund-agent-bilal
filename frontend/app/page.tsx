"use client";

import { AppHeader } from "@/components/layout/AppHeader";
import { SplitView } from "@/components/layout/SplitView";
import { AdminTracePanel } from "@/features/admin/AdminTracePanel";
import { CustomerChatPanel } from "@/features/chat/CustomerChatPanel";
import { useChatSession } from "@/hooks/useChatSession";

export default function HomePage() {
  const chat = useChatSession();

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <AppHeader health={chat.health} sessionId={chat.sessionId} />
      <SplitView
        left={
          <AdminTracePanel
            traceEvents={chat.traceEvents}
            isLoading={chat.isLoading}
            sessionId={chat.sessionId}
          />
        }
        right={
          <CustomerChatPanel
            messages={chat.messages}
            outcome={chat.outcome}
            isLoading={chat.isLoading}
            isInitializing={chat.isInitializing}
            error={chat.error}
            sendMessage={chat.sendMessage}
            resetConversation={chat.resetConversation}
            clearError={chat.clearError}
          />
        }
      />
    </div>
  );
}
