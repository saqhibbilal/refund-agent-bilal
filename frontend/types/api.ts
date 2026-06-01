export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  isStreaming?: boolean;
}

export interface CreateSessionResponse {
  session_id: string;
  customer_email: string | null;
  created_at: string;
}

export interface AgentRecommendation {
  action: "approve" | "deny" | "escalate";
  order_id: string;
  amount_cents: number;
  reason: string;
  rule_ids: string[];
}

export interface DecisionLog {
  id: string;
  session_id: string;
  order_id: string;
  action: AgentRecommendation["action"];
  amount_cents: number;
  reason: string;
  rule_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface DecisionLogsResponse {
  decisions: DecisionLog[];
}

export interface RefundOutcome {
  action: AgentRecommendation["action"];
  order_id: string;
  amount_cents: number;
  reason: string;
  rule_ids: string[];
}

export interface TraceEventItem {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  timestamp: number;
}

export interface HealthResponse {
  status: string;
  data_loaded: boolean;
  llm_configured: boolean;
  database: boolean;
}

export interface DoneEventData {
  response_text: string;
  validation_passed: boolean;
  recommendation: AgentRecommendation | null;
}

export interface ApiErrorBody {
  code: string;
  message: string;
}
