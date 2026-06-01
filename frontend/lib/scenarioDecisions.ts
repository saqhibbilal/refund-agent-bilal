import type { AgentRecommendation } from "@/types/api";

export type ScenarioDecisionAction = AgentRecommendation["action"];

export interface ScenarioDecisionRecord {
  action: ScenarioDecisionAction;
  amountCents: number;
  orderId: string;
  recordedAt: string;
}

const STORAGE_KEY = "worknoon.scenarioDecisions";

export function loadScenarioDecisions(): Record<string, ScenarioDecisionRecord> {
  if (typeof window === "undefined") return {};

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as Record<string, ScenarioDecisionRecord>;
  } catch {
    return {};
  }
}

export function recordScenarioDecision(recommendation: AgentRecommendation): void {
  if (typeof window === "undefined") return;

  const decisions = loadScenarioDecisions();
  decisions[recommendation.order_id] = {
    action: recommendation.action,
    amountCents: recommendation.amount_cents,
    orderId: recommendation.order_id,
    recordedAt: new Date().toISOString(),
  };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(decisions));
}
