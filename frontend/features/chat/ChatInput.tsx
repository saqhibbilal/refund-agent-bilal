"use client";

import { FormEvent, useState } from "react";

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="shrink-0 border-t border-worknoon-ice/15 bg-worknoon-dark/95 p-4"
    >
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your refund request…"
          disabled={disabled}
          className="min-w-0 flex-1 rounded-lg border border-worknoon-ice/20 bg-worknoon-panel px-4 py-2.5 text-chat text-worknoon-ice outline-none placeholder:text-worknoon-ice/35 focus:border-worknoon-ice/45 focus:ring-1 focus:ring-worknoon-ice/25 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="self-start rounded-lg bg-worknoon-ice px-5 py-2.5 text-sm font-semibold text-worknoon-dark transition hover:bg-worknoon-ice/90 disabled:cursor-not-allowed disabled:opacity-40 sm:self-auto sm:w-auto"
        >
          Send
        </button>
      </div>
    </form>
  );
}
