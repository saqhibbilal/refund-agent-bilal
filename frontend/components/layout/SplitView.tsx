import type { ReactNode } from "react";

interface SplitViewProps {
  left: ReactNode;
  right: ReactNode;
}

export function SplitView({ left, right }: SplitViewProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
      <section className="flex min-h-[260px] flex-col border-b border-worknoon-ice/15 lg:min-h-0 lg:w-[35%] lg:border-b-0 lg:border-r">
        {left}
      </section>
      <section className="flex min-h-[420px] flex-col lg:min-h-0 lg:w-[65%]">
        {right}
      </section>
    </div>
  );
}
