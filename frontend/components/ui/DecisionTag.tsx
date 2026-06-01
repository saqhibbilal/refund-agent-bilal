import type { RefundOutcome } from "@/types/api";

type DecisionAction = RefundOutcome["action"];

const CONFIG: Record<
  DecisionAction,
  { label: string; className: string }
> = {
  approve: {
    label: "Approved",
    className:
      "border-worknoon-ice/50 bg-worknoon-ice text-worknoon-dark",
  },
  deny: {
    label: "Denied",
    className: "border-worknoon-ice/30 bg-worknoon-dark text-worknoon-ice",
  },
  escalate: {
    label: "Escalated to human",
    className: "border-worknoon-ice/35 bg-worknoon-ice/12 text-worknoon-ice",
  },
};

interface DecisionTagProps {
  action: DecisionAction;
  className?: string;
}

export function DecisionTag({ action, className = "" }: DecisionTagProps) {
  const { label, className: styles } = CONFIG[action];
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${styles} ${className}`}
    >
      {label}
    </span>
  );
}
