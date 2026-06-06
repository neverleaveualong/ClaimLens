import { create } from "zustand";
import type { AgentEvent } from "@/features/analysis/types/agent-event";

type AnalysisState = {
  description: string;
  events: AgentEvent[];
  setDescription: (description: string) => void;
  addEvent: (event: AgentEvent) => void;
  resetEvents: () => void;
  seedDemoEvents: () => void;
};

const demoEvents: AgentEvent[] = [
  { type: "step_started", step: "input_analysis", message: "Analyzing product description." },
  {
    type: "tool_called",
    step: "input_analysis",
    tool: "extract_product_features",
    data: { features: ["query input", "document retrieval", "answer generation"] },
  },
  { type: "step_completed", step: "input_analysis" },
  { type: "step_started", step: "patent_search", message: "Searching patent candidates." },
  {
    type: "tool_called",
    step: "patent_search",
    tool: "search_patents",
    data: { query: "AI document retrieval answer generation" },
  },
  { type: "step_completed", step: "patent_search" },
  { type: "step_started", step: "claim_parsing", message: "Parsing independent claims." },
  { type: "step_completed", step: "claim_parsing" },
  { type: "step_started", step: "feature_matching", message: "Matching claim elements." },
  {
    type: "claim_chart_row",
    data: {
      claimElement: "Receiving a user query",
      productFeature: "User submits a natural-language question",
      match: "matched",
    },
  },
  { type: "step_completed", step: "feature_matching" },
  { type: "step_started", step: "report_generation", message: "Writing risk review." },
  { type: "step_completed", step: "report_generation" },
  {
    type: "final_report",
    data: {
      markdown:
        "## Draft Risk Review\n\nThe candidate claim shares multiple technical elements with the product flow. This is not a legal infringement decision and requires expert review.",
    },
  },
];

export const useAnalysisStore = create<AnalysisState>((set) => ({
  description: "",
  events: [],
  setDescription: (description) => set({ description }),
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  resetEvents: () => set({ events: [] }),
  seedDemoEvents: () => set({ events: demoEvents }),
}));
