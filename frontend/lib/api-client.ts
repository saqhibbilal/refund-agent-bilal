import type {
  ApiErrorBody,
  CreateSessionResponse,
  DecisionLogsResponse,
  HealthResponse,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function getApiBaseUrl(): string {
  return API_BASE.replace(/\/$/, "");
}

async function parseError(response: Response): Promise<ApiErrorBody> {
  try {
    return (await response.json()) as ApiErrorBody;
  } catch {
    return { code: "UNKNOWN", message: response.statusText || "Request failed" };
  }
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getApiBaseUrl()}/health`);
  if (!response.ok) {
    const err = await parseError(response);
    throw new Error(err.message);
  }
  return response.json() as Promise<HealthResponse>;
}

export async function fetchDecisionLogs(): Promise<DecisionLogsResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/chat/decisions`);
  if (!response.ok) {
    const err = await parseError(response);
    throw new Error(err.message);
  }
  return response.json() as Promise<DecisionLogsResponse>;
}

export async function createSession(
  customerEmail?: string,
): Promise<CreateSessionResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/chat/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_email: customerEmail ?? null }),
  });
  if (!response.ok) {
    const err = await parseError(response);
    throw new Error(err.message);
  }
  return response.json() as Promise<CreateSessionResponse>;
}

export async function sendMessageStream(
  sessionId: string,
  content: string,
  clientMessageId?: string,
): Promise<Response> {
  const response = await fetch(
    `${getApiBaseUrl()}/api/chat/sessions/${sessionId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        content,
        client_message_id: clientMessageId ?? null,
      }),
    },
  );
  if (!response.ok) {
    const err = await parseError(response);
    throw new Error(err.message);
  }
  if (!response.body) {
    throw new Error("No response body for SSE stream");
  }
  return response;
}
