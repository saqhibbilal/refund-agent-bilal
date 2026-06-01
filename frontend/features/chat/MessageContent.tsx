import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";

interface MessageContentProps {
  content: string;
  isStreaming?: boolean;
}

const markdownComponents = {
  p: ({ children }: { children?: ReactNode }) => (
    <p className="mb-3 last:mb-0">{children}</p>
  ),
  ul: ({ children }: { children?: ReactNode }) => (
    <ul className="mb-3 list-disc space-y-1.5 pl-5 last:mb-0">{children}</ul>
  ),
  ol: ({ children }: { children?: ReactNode }) => (
    <ol className="mb-3 list-decimal space-y-1.5 pl-5 last:mb-0">{children}</ol>
  ),
  li: ({ children }: { children?: ReactNode }) => (
    <li className="leading-relaxed">{children}</li>
  ),
  strong: ({ children }: { children?: ReactNode }) => (
    <strong className="font-semibold text-worknoon-ice">{children}</strong>
  ),
  em: ({ children }: { children?: ReactNode }) => (
    <em className="italic text-worknoon-ice/80">{children}</em>
  ),
};

export function MessageContent({ content, isStreaming }: MessageContentProps) {
  return (
    <div className="message-markdown break-words text-chat leading-relaxed">
      <ReactMarkdown components={markdownComponents}>{content}</ReactMarkdown>
      {isStreaming && (
        <span className="ml-0.5 inline-block h-4 w-1 animate-pulse bg-worknoon-ice/45 align-middle" />
      )}
    </div>
  );
}
