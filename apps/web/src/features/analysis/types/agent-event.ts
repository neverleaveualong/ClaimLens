export type AgentEventType =
  | "step_started"
  | "tool_called"
  | "tool_result"
  | "step_completed"
  | "claim_chart_row"
  | "final_report"
  | "error";

export type AgentEvent = {
  type: AgentEventType;
  step?: string | null;
  tool?: string | null;
  message?: string | null;
  data?: Record<string, unknown> | null;
};
