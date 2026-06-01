"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Refund Agent" },
  { href: "/analytics", label: "Data & Analytics" },
  { href: "/policy", label: "Policy Docs" },
] as const;

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="scroll-area flex max-w-full gap-1 overflow-x-auto rounded-lg border border-worknoon-ice/15 bg-worknoon-ice/[0.055] p-1">
      {LINKS.map(({ href, label }) => {
        const active =
          href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={`shrink-0 rounded-md px-3 py-1.5 text-sm font-medium transition ${
              active
                ? "bg-worknoon-ice text-worknoon-dark"
                : "text-worknoon-ice/70 hover:bg-worknoon-ice/10 hover:text-worknoon-ice"
            }`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
