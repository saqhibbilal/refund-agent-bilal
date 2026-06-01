import { AppNav } from "@/components/layout/AppNav";

const POLICY_SECTIONS = [
  {
    id: "RULE-CUSTOMER-VERIFY",
    title: "Customer Verification",
    summary:
      "The agent needs enough information to locate the order or customer record before checking eligibility. Useful identifiers include order ID, account email, or customer ID.",
  },
  {
    id: "RULE-RET-30",
    title: "30-Day Return Window",
    summary:
      "Standard physical products may be returned within 30 calendar days of the recorded delivery date when the order is delivered, not final sale, not an activated digital warranty, and not already refunded.",
  },
  {
    id: "RULE-FINAL-SALE",
    title: "Final Sale and Clearance",
    summary:
      "Products marked final sale, including open-box clearance items, are non-refundable except where required by law. Customer tier or preference does not override this rule.",
  },
  {
    id: "RULE-DOA-7",
    title: "Dead on Arrival",
    summary:
      "A product reported dead on arrival within 7 calendar days of delivery may qualify for a full refund or replacement, while still respecting hard exclusions like final sale or activated warranties.",
  },
  {
    id: "RULE-WARRANTY-DIGITAL",
    title: "Digital Warranty Products",
    summary:
      "Extended warranties and digital protection plans are non-refundable once activated. Unactivated plans follow the standard return-window rules.",
  },
  {
    id: "RULE-ONE-REFUND",
    title: "One Refund Per Order",
    summary:
      "Each order can have at most one refund event. Orders with a partial or full refund already on record cannot receive another automated refund.",
  },
  {
    id: "RULE-ESC-500",
    title: "High-Value Review",
    summary:
      "Eligible refund amounts above $500 require human specialist review before approval. This is a review requirement, not an automatic denial.",
  },
  {
    id: "RULE-RESTOCK-LAPTOP",
    title: "Laptop Restocking Fee",
    summary:
      "Opened or used Worknoon laptops are subject to a 15% restocking fee deducted from the eligible refund amount.",
  },
  {
    id: "RULE-FRAUD-OWNERSHIP",
    title: "Ownership Verification",
    summary:
      "Customer email, customer ID, order ownership, and serial numbers must match authoritative records. Mismatches require human verification before any refund decision.",
  },
  {
    id: "RULE-VIP-CARE",
    title: "VIP Customer Care",
    summary:
      "VIP customers receive clearer explanations and priority routing when review is needed, but VIP status does not override hard policy rules.",
  },
] as const;

export default function PolicyPage() {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-worknoon-dark">
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-worknoon-ice/15 bg-worknoon-dark/95 px-5 py-4 shadow-[0_1px_30px_rgba(214,239,255,0.08)] lg:px-6">
        <div>
          <h1 className="font-display text-xl font-semibold uppercase tracking-wide text-worknoon-ice lg:text-2xl">
            Worknoon Refund Agent
          </h1>
          <p className="mt-0.5 text-sm text-worknoon-ice/55">
            Policy Docs · Customer-facing refund rules
          </p>
        </div>
        <AppNav />
      </header>

      <main className="scroll-area flex-1 overflow-y-auto px-5 py-6 lg:px-8">
        <section className="rounded-2xl border border-worknoon-ice/15 bg-gradient-to-br from-worknoon-ice/[0.11] to-worknoon-ice/[0.025] p-6 shadow-2xl shadow-[rgba(214,239,255,0.08)]">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-worknoon-ice/50">
            Current company policy
          </p>
          <h2 className="mt-2 font-display text-3xl font-semibold text-worknoon-ice">
            Refund Policy
          </h2>
          <p className="mt-3 max-w-3xl text-chat leading-relaxed text-worknoon-ice/70">
            Effective January 1, 2025. These rules explain how Worknoon handles
            refund requests for electronics, accessories, digital protection
            plans, and clearance or open-box products. The refund agent may
            explain these rules, but final automated decisions must be based on
            verified order records and deterministic policy checks.
          </p>
        </section>

        <section className="mt-8 grid gap-4 lg:grid-cols-2">
          {POLICY_SECTIONS.map((section) => (
            <article
              key={section.id}
              className="rounded-xl border border-worknoon-ice/15 bg-worknoon-panel p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <h3 className="font-display text-xl font-semibold text-worknoon-ice">
                  {section.title}
                </h3>
                <span className="rounded border border-worknoon-ice/25 bg-worknoon-dark px-2 py-1 font-mono text-xs font-semibold text-worknoon-ice/75">
                  {section.id}
                </span>
              </div>
              <p className="mt-3 text-chat leading-relaxed text-worknoon-ice/70">
                {section.summary}
              </p>
            </article>
          ))}
        </section>

        <section className="mt-8 rounded-xl border border-worknoon-ice/15 bg-worknoon-panel p-5">
          <h3 className="font-display text-xl font-semibold text-worknoon-ice">
            How Decisions Happen
          </h3>
          <p className="mt-3 max-w-3xl text-chat leading-relaxed text-worknoon-ice/70">
            A policy rule is not a verdict by itself. The customer must provide
            enough order context, the agent must verify the record, and the
            eligibility check must run before a request can be approved, denied,
            or escalated to a human specialist.
          </p>
        </section>
      </main>
    </div>
  );
}
