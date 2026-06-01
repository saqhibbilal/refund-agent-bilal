import { fetchDecisionLogs } from "./api-client";
import {
  loadScenarioDecisions,
  type ScenarioDecisionRecord,
} from "./scenarioDecisions";

export interface CrmCustomer {
  id: string;
  name: string;
  email: string;
  tier: string;
  notes: string | null;
}

export interface CrmOrder {
  order_id: string;
  customer_id: string;
  total_cents: number;
  status: string;
  purchase_date: string;
  delivered_at: string | null;
  refund_status: "none" | "partial" | "full";
  items: {
    category: string;
    final_sale: boolean;
    name: string;
    price_cents: number;
    sku: string;
    warranty_activated: boolean;
  }[];
}

export interface CustomerRow {
  id: string;
  name: string;
  email: string;
  tier: string;
  notes: string | null;
  orderCount: number;
  totalSpentCents: number;
  previousRefundCount: number;
  riskScore: number;
  riskLevel: "low" | "medium" | "high";
  hasRefund: boolean;
}

export interface ScenarioOrderCard {
  orderId: string;
  customerId: string;
  customerName: string;
  customerTier: string;
  purchaseDate: string;
  daysSincePurchase: number;
  totalCents: number;
  status: string;
  riskSignal: "pass" | "review";
  decisionLog: "Not evaluated" | "Approved" | "Denied" | "Escalated";
  decisionAmountCents: number | null;
  localReference: string;
  items: {
    name: string;
    priceCents: number;
    sku: string;
  }[];
}

export interface AnalyticsOverview {
  totalCustomers: number;
  totalOrders: number;
  totalRevenueCents: number;
  vipCustomers: number;
  refundNone: number;
  refundPartial: number;
  refundFull: number;
  finalSaleOrders: number;
  deliveredOrders: number;
  customerRows: CustomerRow[];
  refundOrders: { orderId: string; status: string; totalCents: number }[];
  scenarioCards: ScenarioOrderCard[];
}

function formatMoney(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

export { formatMoney };

export async function loadAnalyticsOverview(): Promise<AnalyticsOverview> {
  const [customersRes, ordersRes] = await Promise.all([
    fetch("/crm/customers.json"),
    fetch("/crm/orders.json"),
  ]);
  if (!customersRes.ok || !ordersRes.ok) {
    throw new Error("Could not load business data");
  }
  const customersData = (await customersRes.json()) as { customers: CrmCustomer[] };
  const ordersData = (await ordersRes.json()) as { orders: CrmOrder[] };
  const customers = customersData.customers;
  const orders = ordersData.orders;

  const ordersByCustomer = new Map<string, CrmOrder[]>();
  for (const order of orders) {
    const list = ordersByCustomer.get(order.customer_id) ?? [];
    list.push(order);
    ordersByCustomer.set(order.customer_id, list);
  }

  const customerRows: CustomerRow[] = customers.map((c) => {
    const custOrders = ordersByCustomer.get(c.id) ?? [];
    const totalSpentCents = custOrders.reduce((s, o) => s + o.total_cents, 0);
    const previousRefundCount = custOrders.filter((o) => o.refund_status !== "none").length;
    const hasRefund = previousRefundCount > 0;
    const notes = (c.notes ?? "").toLowerCase();
    const riskScore = Math.min(
      100,
      previousRefundCount * 25
        + (notes.includes("dispute") ? 20 : 0)
        + (notes.includes("frequent") ? 10 : 0),
    );
    const riskLevel = riskScore >= 60 ? "high" : riskScore >= 25 ? "medium" : "low";
    return {
      id: c.id,
      name: c.name,
      email: c.email,
      tier: c.tier,
      notes: c.notes,
      orderCount: custOrders.length,
      totalSpentCents,
      previousRefundCount,
      riskScore,
      riskLevel,
      hasRefund,
    };
  });

  customerRows.sort((a, b) => b.totalSpentCents - a.totalSpentCents);

  const customersById = new Map(customers.map((customer) => [customer.id, customer]));
  const customerSignalsById = new Map(customerRows.map((row) => [row.id, row]));
  const decisionsByOrderId = await loadDecisionLogsWithFallback();
  const now = new Date();
  const scenarioCards: ScenarioOrderCard[] = orders.slice(0, 6).map((order) => {
    const customer = customersById.get(order.customer_id);
    const signal = customerSignalsById.get(order.customer_id);
    const decision = decisionsByOrderId[order.order_id];
    const purchaseDate = new Date(order.purchase_date);
    const daysSincePurchase = Number.isNaN(purchaseDate.getTime())
      ? 0
      : Math.max(
          0,
          Math.floor((now.getTime() - purchaseDate.getTime()) / 86_400_000),
        );

    return {
      orderId: order.order_id,
      customerId: order.customer_id,
      customerName: customer?.name ?? "Unknown customer",
      customerTier: customer?.tier ?? "standard",
      purchaseDate: order.purchase_date,
      daysSincePurchase,
      totalCents: order.total_cents,
      status: order.status,
      riskSignal: signal?.riskLevel === "high" ? "review" : "pass",
      decisionLog: decision ? formatDecisionLog(decision.action) : "Not evaluated",
      decisionAmountCents: decision?.amountCents ?? null,
      localReference: order.refund_status === "none"
        ? "No prior refund"
        : `${order.refund_status} refund on record`,
      items: order.items.map((item) => ({
        name: item.name,
        priceCents: item.price_cents,
        sku: item.sku,
      })),
    };
  });

  return {
    totalCustomers: customers.length,
    totalOrders: orders.length,
    totalRevenueCents: orders.reduce((s, o) => s + o.total_cents, 0),
    vipCustomers: customers.filter((c) => c.tier === "vip").length,
    refundNone: orders.filter((o) => o.refund_status === "none").length,
    refundPartial: orders.filter((o) => o.refund_status === "partial").length,
    refundFull: orders.filter((o) => o.refund_status === "full").length,
    finalSaleOrders: orders.filter((o) =>
      o.items.some((i) => i.final_sale),
    ).length,
    deliveredOrders: orders.filter((o) => o.status === "delivered").length,
    customerRows,
    refundOrders: orders
      .filter((o) => o.refund_status !== "none")
      .map((o) => ({
        orderId: o.order_id,
        status: o.refund_status,
        totalCents: o.total_cents,
      })),
    scenarioCards,
  };
}

function formatDecisionLog(action: "approve" | "deny" | "escalate"): ScenarioOrderCard["decisionLog"] {
  if (action === "approve") return "Approved";
  if (action === "deny") return "Denied";
  return "Escalated";
}

async function loadDecisionLogsWithFallback(): Promise<Record<string, ScenarioDecisionRecord>> {
  const localDecisions = loadScenarioDecisions();
  try {
    const response = await fetchDecisionLogs();
    return response.decisions.reduce(
      (acc: Record<string, ScenarioDecisionRecord>, decision) => {
        acc[decision.order_id] = {
          action: decision.action,
          amountCents: decision.amount_cents,
          orderId: decision.order_id,
          recordedAt: decision.updated_at,
        };
        return acc;
      },
      { ...localDecisions },
    );
  } catch {
    return localDecisions;
  }
}
