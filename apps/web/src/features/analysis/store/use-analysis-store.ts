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
  { type: "step_started", step: "input_analysis", message: "제품/기술 설명을 분석하는 중입니다." },
  {
    type: "tool_called",
    step: "input_analysis",
    tool: "extract_product_features",
    data: { features: ["질문 입력", "문서 검색", "답변 생성"] },
  },
  { type: "step_completed", step: "input_analysis" },
  { type: "step_started", step: "patent_search", message: "특허 후보를 검색하는 중입니다." },
  {
    type: "tool_called",
    step: "patent_search",
    tool: "search_patents",
    data: { query: "AI 문서 검색 답변 생성" },
  },
  { type: "step_completed", step: "patent_search" },
  { type: "step_started", step: "claim_parsing", message: "독립항을 분석하는 중입니다." },
  { type: "step_completed", step: "claim_parsing" },
  { type: "step_started", step: "feature_matching", message: "청구항 구성요소를 제품 기능과 비교하는 중입니다." },
  {
    type: "claim_chart_row",
    data: {
      claimElement: "사용자 질문을 수신함",
      productFeature: "사용자가 자연어 질문을 입력함",
      match: "matched",
    },
  },
  { type: "step_completed", step: "feature_matching" },
  { type: "step_started", step: "report_generation", message: "기술 검토 리포트를 작성하는 중입니다." },
  { type: "step_completed", step: "report_generation" },
  {
    type: "final_report",
    data: {
      markdown:
        "## 기술 검토 초안\n\n후보 청구항은 제품 흐름과 여러 기술 구성요소가 겹칩니다. 이 결과는 법률적 침해 판단이 아니며 전문가 검토가 필요합니다.",
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
