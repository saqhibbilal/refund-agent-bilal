import type { ChatSuggestion } from "./demoSuggestions";

interface SuggestionPanelProps {
  title: string;
  subtitle?: string;
  suggestions: ChatSuggestion[];
  onSelect: (prompt: string) => void;
  disabled?: boolean;
  variant?: "cards" | "chips";
}

export function SuggestionPanel({
  title,
  subtitle,
  suggestions,
  onSelect,
  disabled = false,
  variant = "chips",
}: SuggestionPanelProps) {
  if (suggestions.length === 0) return null;

  const isCards = variant === "cards";

  return (
    <section
      className={`shrink-0 border-worknoon-ice/15 ${
        isCards ? "border-b px-4 py-3" : "border-t px-4 py-3"
      }`}
    >
      <div className={isCards ? "mb-2" : "mb-3"}>
        <h3 className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-worknoon-ice/60">
          {title}
        </h3>
        {subtitle && (
          <p className="mt-0.5 text-xs leading-relaxed text-worknoon-ice/45">{subtitle}</p>
        )}
      </div>

      <div
        className={
          isCards
            ? "grid gap-1.5 sm:grid-cols-2 xl:grid-cols-4"
            : "flex flex-wrap gap-2"
        }
      >
        {suggestions.map((suggestion) => (
          <button
            key={suggestion.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(suggestion.prompt)}
            className={
              isCards
                ? "rounded-lg border border-worknoon-ice/15 bg-worknoon-ice/[0.045] px-2.5 py-2 text-left transition hover:border-worknoon-ice/35 hover:bg-worknoon-ice/[0.085] disabled:cursor-not-allowed disabled:opacity-50"
                : "rounded-full border border-worknoon-ice/15 bg-worknoon-ice/[0.05] px-3 py-1.5 text-left text-xs font-medium text-worknoon-ice/75 transition hover:border-worknoon-ice/35 hover:bg-worknoon-ice/[0.085] disabled:cursor-not-allowed disabled:opacity-50"
            }
          >
            <span
              className={
                isCards
                  ? "block truncate text-xs font-semibold text-worknoon-ice"
                  : "block whitespace-nowrap"
              }
            >
              {suggestion.label}
            </span>
            {isCards && suggestion.description && (
              <span className="mt-0.5 block truncate text-[0.68rem] leading-relaxed text-worknoon-ice/45">
                {suggestion.description}
              </span>
            )}
          </button>
        ))}
      </div>
    </section>
  );
}
