import type { ReactNode } from "react";

interface SplitViewProps {
  left: ReactNode;
  right: ReactNode;
}

export function SplitView({ left, right }: SplitViewProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto lg:flex-row lg:overflow-hidden">
      <section className="flex min-h-[260px] shrink-0 flex-col border-b border-worknoon-ice/15 lg:min-h-0 lg:w-[35%] lg:shrink lg:border-b-0 lg:border-r">
        {left}
      </section>
      <section className="flex min-h-[420px] shrink-0 flex-col lg:min-h-0 lg:w-[65%] lg:shrink">
        {right}
      </section>
    </div>
  );
}
