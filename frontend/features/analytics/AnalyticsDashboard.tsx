"use client";

import { useEffect, useState } from "react";

import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import {
  formatMoney,
  loadAnalyticsOverview,
  type AnalyticsOverview,
  type ScenarioOrderCard,
} from "@/lib/crmAnalytics";

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-worknoon-ice/15 bg-worknoon-panel p-5 shadow-[0_16px_40px_rgba(214,239,255,0.05)]">
      <p className="text-xs font-semibold uppercase tracking-wider text-worknoon-ice/50">
        {label}
      </p>
      <p className="mt-2 font-display text-3xl font-semibold text-worknoon-ice">{value}</p>
      {hint && <p className="mt-1 text-sm text-worknoon-ice/55">{hint}</p>}
    </div>
  );
}

function DonutChart({
  segments,
}: {
  segments: { label: string; value: number; color: string }[];
}) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);
  let cursor = 0;
  const gradient = segments
    .map((segment) => {
      const start = cursor;
      const size = total > 0 ? (segment.value / total) * 100 : 0;
      cursor += size;
      return `${segment.color} ${start}% ${cursor}%`;
    })
    .join(", ");

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row">
      <div
        className="relative grid h-36 w-36 shrink-0 place-items-center rounded-full"
        style={{ background: `conic-gradient(${gradient})` }}
      >
        <div className="grid h-24 w-24 place-items-center rounded-full bg-worknoon-dark shadow-[inset_0_0_24px_rgba(214,239,255,0.14)]">
          <div className="text-center">
            <p className="font-display text-2xl font-semibold text-worknoon-ice">{total}</p>
            <p className="text-[0.65rem] uppercase tracking-wider text-worknoon-ice/45">orders</p>
          </div>
        </div>
      </div>
      <div className="w-full space-y-2">
        {segments.map((segment) => (
          <div key={segment.label} className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2 text-sm text-worknoon-ice/70">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: segment.color }}
              />
              {segment.label}
            </span>
            <span className="font-mono text-sm font-semibold text-worknoon-ice">
              {segment.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BarRow({
  label,
  value,
  max,
  colorClass = "bg-worknoon-ice",
}: {
  label: string;
  value: number;
  max: number;
  colorClass?: string;
}) {
  const width = max > 0 ? Math.max((value / max) * 100, 4) : 0;

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3 text-sm">
        <span className="truncate text-worknoon-ice/70">{label}</span>
        <span className="font-mono text-worknoon-ice/80">{value}</span>
      </div>
      <div className="h-2 rounded-full bg-worknoon-ice/10">
        <div
          className={`h-2 rounded-full ${colorClass}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

function MiniMetric({
  label,
  value,
  tone = "quiet",
}: {
  label: string;
  value: string;
  tone?: "quiet" | "solid" | "glow";
}) {
  const toneClass = {
    quiet: "border-worknoon-ice/15 bg-worknoon-ice/[0.045] text-worknoon-ice",
    solid: "border-worknoon-ice bg-worknoon-ice text-worknoon-dark",
    glow: "border-worknoon-ice/35 bg-worknoon-ice/12 text-worknoon-ice",
  }[tone];

  return (
    <div className={`rounded-xl border px-4 py-3 ${toneClass}`}>
      <p className="text-[0.68rem] uppercase tracking-wider opacity-60">{label}</p>
      <p className="mt-1 font-display text-2xl font-semibold">{value}</p>
    </div>
  );
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function ScenarioOrderCard({ scenario }: { scenario: ScenarioOrderCard }) {
  const evaluated = scenario.decisionLog !== "Not evaluated";

  return (
    <article className="rounded-2xl border border-worknoon-ice/15 bg-worknoon-dark/80 p-4 shadow-[0_18px_44px_rgba(214,239,255,0.06)]">
      <div className="flex items-start justify-between gap-3 border-b border-worknoon-ice/10 pb-3">
        <div>
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-worknoon-ice/45">
            Support session dialogue
          </p>
          <h3 className="mt-1 font-display text-xl font-semibold text-worknoon-ice">
            {scenario.customerName}
          </h3>
          <p className="font-mono text-xs uppercase text-worknoon-ice/45">
            {scenario.customerId} · {scenario.customerTier}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-worknoon-ice/45">
            Fraud risk eval
          </p>
          <span
            className={`mt-1 inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase ${
              scenario.riskSignal === "pass"
                ? "border-worknoon-ice bg-worknoon-ice text-worknoon-dark"
                : "border-worknoon-ice/35 bg-worknoon-ice/10 text-worknoon-ice"
            }`}
          >
            {scenario.riskSignal}
          </span>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between gap-3">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-worknoon-ice/45">
          Purchases registry [{scenario.items.length}]
        </p>
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-worknoon-ice/45">
          Local reference
        </p>
      </div>

      <div className="mt-2 rounded-xl border border-worknoon-ice/10 bg-worknoon-ice/[0.035] p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="font-mono text-sm font-semibold text-worknoon-ice">
            {scenario.orderId}
          </span>
          <span className="font-mono text-xs text-worknoon-ice/55">
            Date: {formatDate(scenario.purchaseDate)} ({scenario.daysSincePurchase} days ago)
          </span>
        </div>

        <div className="mt-3 space-y-2">
          {scenario.items.map((item) => (
            <div
              key={`${scenario.orderId}-${item.sku}`}
              className="flex items-start justify-between gap-3 text-sm"
            >
              <div>
                <p className="font-medium text-worknoon-ice">{item.name}</p>
                <p className="font-mono text-xs text-worknoon-ice/45">{item.sku}</p>
              </div>
              <span className="font-mono text-worknoon-ice">
                {formatMoney(item.priceCents)}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-worknoon-ice/10 pt-3">
          <span className="text-sm text-worknoon-ice/70">
            Total purchase:{" "}
            <strong className="font-mono text-worknoon-ice">
              {formatMoney(scenario.totalCents)}
            </strong>
          </span>
          <span
            className={`rounded border px-2 py-1 font-mono text-xs font-semibold uppercase ${
              evaluated
                ? "border-worknoon-ice bg-worknoon-ice text-worknoon-dark"
                : "border-worknoon-ice/25 bg-worknoon-ice/10 text-worknoon-ice"
            }`}
          >
            Decision log: {scenario.decisionLog}
            {scenario.decisionAmountCents
              ? ` · ${formatMoney(scenario.decisionAmountCents)}`
              : ""}
          </span>
        </div>
      </div>

      <p className="mt-3 text-xs text-worknoon-ice/50">
        {scenario.localReference} · order status: {scenario.status}
      </p>
    </article>
  );
}

export function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalyticsOverview()
      .then(setData)
      .catch(() => setError("Could not load business data. Refresh to try again."));
  }, []);

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-center text-worknoon-ice">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-1 items-center justify-center py-24">
        <LoadingSpinner size="lg" label="Loading business data…" />
      </div>
    );
  }

  const refundRate =
    data.totalOrders > 0
      ? Math.round(
          ((data.refundPartial + data.refundFull) / data.totalOrders) * 100,
        )
      : 0;
  const vipRate =
    data.totalCustomers > 0
      ? Math.round((data.vipCustomers / data.totalCustomers) * 100)
      : 0;
  const deliveryRate =
    data.totalOrders > 0
      ? Math.round((data.deliveredOrders / data.totalOrders) * 100)
      : 0;
  const refundSegments = [
    { label: "No refund", value: data.refundNone, color: "#D6EFFF" },
    { label: "Partial", value: data.refundPartial, color: "rgba(214,239,255,0.64)" },
    { label: "Full", value: data.refundFull, color: "rgba(214,239,255,0.34)" },
  ];
  const topCustomers = data.customerRows.slice(0, 5);
  const topSpend = Math.max(...topCustomers.map((row) => row.totalSpentCents), 0);

  return (
    <div className="scroll-area flex-1 overflow-y-auto px-5 py-6 lg:px-8">
      <p className="mb-6 max-w-2xl text-chat text-worknoon-ice/65">
        A snapshot of Worknoon customer and order records. This page shows
        historical context only; live decisions are created after a customer
        request is evaluated in the refund agent flow.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Customers" value={String(data.totalCustomers)} hint="Active accounts in CRM" />
        <StatCard label="Orders" value={String(data.totalOrders)} hint={`${data.deliveredOrders} delivered`} />
        <StatCard
          label="Gross sales"
          value={formatMoney(data.totalRevenueCents)}
          hint="All orders combined"
        />
        <StatCard
          label="VIP customers"
          value={String(data.vipCustomers)}
          hint="Priority support tier"
        />
      </div>

      <section className="mt-8 rounded-2xl border border-worknoon-ice/15 bg-worknoon-panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-worknoon-ice/50">
              Scenario registry
            </p>
            <h2 className="mt-1 font-display text-2xl font-semibold text-worknoon-ice">
              Order cards awaiting evaluation
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-worknoon-ice/55">
              These cards mirror reviewer scenarios from CRM records. They stay
              marked as Not evaluated until a customer request is actually run
              through the refund agent.
            </p>
          </div>
          <span className="rounded-full border border-worknoon-ice/25 bg-worknoon-dark px-3 py-1 font-mono text-xs font-semibold uppercase text-worknoon-ice">
            Default state: Not evaluated
          </span>
        </div>
        <div className="mt-5 grid gap-4 xl:grid-cols-2">
          {data.scenarioCards.map((scenario) => (
            <ScenarioOrderCard key={scenario.orderId} scenario={scenario} />
          ))}
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-worknoon-ice/15 bg-gradient-to-br from-worknoon-ice/[0.11] to-worknoon-ice/[0.025] p-5 shadow-2xl shadow-[rgba(214,239,255,0.08)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-worknoon-ice/50">
              Infographics
            </p>
            <h2 className="mt-1 font-display text-2xl font-semibold text-worknoon-ice">
              Business records snapshot
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-worknoon-ice/55">
              A quick visual view of existing refund history, VIP mix, and customer
              value before any new request is evaluated.
            </p>
          </div>
          <div className="grid min-w-[260px] flex-1 grid-cols-3 gap-2">
            <MiniMetric label="Recorded refunds" value={`${refundRate}%`} tone="glow" />
            <MiniMetric label="Delivered" value={`${deliveryRate}%`} tone="solid" />
            <MiniMetric label="VIP mix" value={`${vipRate}%`} />
          </div>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-xl border border-worknoon-ice/15 bg-worknoon-dark/50 p-4">
            <h3 className="font-display text-lg font-semibold text-worknoon-ice">
              Recorded refund history
            </h3>
            <p className="mb-4 mt-1 text-sm text-worknoon-ice/50">
              Shows prior refund activity already stored on orders, not new
              approval or denial decisions.
            </p>
            <DonutChart segments={refundSegments} />
          </div>

          <div className="rounded-xl border border-worknoon-ice/15 bg-worknoon-dark/50 p-4">
            <h3 className="font-display text-lg font-semibold text-worknoon-ice">
              Top customer value
            </h3>
            <p className="mb-4 mt-1 text-sm text-worknoon-ice/50">
              Highest lifetime spend accounts, useful as neutral support context.
            </p>
            <div className="space-y-3">
              {topCustomers.map((row) => (
                <BarRow
                  key={row.id}
                  label={`${row.name}${row.tier === "vip" ? " · VIP" : ""}`}
                  value={Math.round(row.totalSpentCents / 100)}
                  max={Math.round(topSpend / 100)}
                  colorClass={row.tier === "vip" ? "bg-worknoon-ice" : "bg-worknoon-ice/55"}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-worknoon-ice/15 bg-worknoon-panel p-5">
          <h2 className="font-display text-lg font-semibold text-worknoon-ice">
            Existing refund records
          </h2>
          <p className="mt-1 text-sm text-worknoon-ice/55">
            {refundRate}% of orders have a partial or full refund already on record
          </p>
          <ul className="mt-5 space-y-3 text-chat">
            <li className="flex justify-between border-b border-worknoon-ice/15 pb-2">
              <span className="text-worknoon-ice/70">No refund on record</span>
              <span className="font-semibold text-worknoon-ice">{data.refundNone}</span>
            </li>
            <li className="flex justify-between border-b border-worknoon-ice/15 pb-2">
              <span className="text-worknoon-ice/70">Partial refund</span>
              <span className="font-semibold text-worknoon-ice/80">{data.refundPartial}</span>
            </li>
            <li className="flex justify-between border-b border-worknoon-ice/15 pb-2">
              <span className="text-worknoon-ice/70">Full refund</span>
              <span className="font-semibold text-worknoon-ice/65">{data.refundFull}</span>
            </li>
            <li className="flex justify-between pt-1">
              <span className="text-worknoon-ice/70">Final-sale items in catalog</span>
              <span className="font-semibold text-worknoon-ice">{data.finalSaleOrders}</span>
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-worknoon-ice/15 bg-worknoon-panel p-5">
          <h2 className="font-display text-lg font-semibold text-worknoon-ice">
            Orders with recorded refunds
          </h2>
          <p className="mt-1 text-sm text-worknoon-ice/55">
            These are historical records only. New requests still need to run
            through the agent before any verdict appears.
          </p>
          {data.refundOrders.length === 0 ? (
            <p className="mt-5 text-sm text-worknoon-ice/45">None on record.</p>
          ) : (
            <ul className="mt-5 space-y-2 text-chat">
              {data.refundOrders.map((o) => (
                <li
                  key={o.orderId}
                  className="flex justify-between rounded-lg border border-worknoon-ice/15 bg-worknoon-ice/5 px-3 py-2"
                >
                  <span className="font-mono text-worknoon-ice">{o.orderId}</span>
                  <span className="capitalize text-worknoon-ice/70">
                    {o.status} · {formatMoney(o.totalCents)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="mt-8 rounded-xl border border-worknoon-ice/15 bg-worknoon-panel p-5">
        <h2 className="font-display text-lg font-semibold text-worknoon-ice">
          Customers
        </h2>
        <p className="mt-1 text-sm text-worknoon-ice/55">
          Sorted by lifetime spend. These signals help support review, but they
          are not approval or denial decisions.
        </p>
        <div className="scroll-area mt-4 overflow-x-auto">
          <table className="w-full min-w-[880px] text-left text-chat">
            <thead>
              <tr className="border-b border-worknoon-ice/20 text-xs uppercase tracking-wider text-worknoon-ice/50">
                <th className="pb-3 pr-4 font-semibold">Name</th>
                <th className="pb-3 pr-4 font-semibold">Email</th>
                <th className="pb-3 pr-4 font-semibold">Tier</th>
                <th className="pb-3 pr-4 font-semibold text-right">Orders</th>
                <th className="pb-3 pr-4 font-semibold text-right">Spent</th>
                <th className="pb-3 pr-4 font-semibold text-right">Previous refunds</th>
                <th className="pb-3 pr-4 font-semibold">Account signal</th>
                <th className="pb-3 font-semibold">Notes</th>
              </tr>
            </thead>
            <tbody>
              {data.customerRows.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-worknoon-ice/10 text-worknoon-ice/85 last:border-0"
                >
                  <td className="py-3 pr-4 font-medium text-worknoon-ice">{row.name}</td>
                  <td className="py-3 pr-4 text-worknoon-ice/65">{row.email}</td>
                  <td className="py-3 pr-4 capitalize">
                    <span
                      className={
                        row.tier === "vip"
                          ? "rounded bg-worknoon-ice px-2 py-0.5 text-xs font-semibold uppercase text-worknoon-dark"
                          : "text-worknoon-ice/55"
                      }
                    >
                      {row.tier}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-right">{row.orderCount}</td>
                  <td className="py-3 pr-4 text-right font-medium">
                    {formatMoney(row.totalSpentCents)}
                  </td>
                  <td className="py-3 pr-4 text-right">
                    {row.previousRefundCount}
                  </td>
                  <td className="py-3 pr-4">
                    <span
                      className={
                        row.riskLevel === "high"
                          ? "rounded border border-worknoon-ice/35 bg-worknoon-dark px-2 py-0.5 text-xs font-semibold uppercase text-worknoon-ice"
                          : row.riskLevel === "medium"
                            ? "rounded border border-worknoon-ice/30 bg-worknoon-ice/10 px-2 py-0.5 text-xs font-semibold uppercase text-worknoon-ice"
                            : "rounded bg-worknoon-ice px-2 py-0.5 text-xs font-semibold uppercase text-worknoon-dark"
                      }
                    >
                      {row.riskScore} · {row.riskLevel}
                    </span>
                  </td>
                  <td className="py-3 text-worknoon-ice/55">
                    {row.notes ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
