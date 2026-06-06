"use client";

import { useMemo } from "react";
import { useAnalysisStore } from "@/features/analysis/store/use-analysis-store";

const steps = [
  { id: "input_analysis", label: "Input Analysis" },
  { id: "patent_search", label: "Patent Search" },
  { id: "claim_parsing", label: "Claim Parsing" },
  { id: "feature_matching", label: "Feature Matching" },
  { id: "report_generation", label: "Report" },
];

export default function Home() {
  const { description, setDescription, events, seedDemoEvents } = useAnalysisStore();

  const completedSteps = useMemo(
    () => new Set(events.filter((event) => event.type === "step_completed").map((event) => event.step)),
    [events],
  );

  const chartRows = events.filter((event) => event.type === "claim_chart_row");
  const report = events.findLast((event) => event.type === "final_report");

  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d8d3c6] bg-[#ffffff]/85">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#5e6f64]">
              AI Patent Risk Agent
            </p>
            <h1 className="text-2xl font-semibold tracking-normal text-[#1f2328]">
              ClaimLens
            </h1>
          </div>
          <div className="rounded-md border border-[#c9c3b4] bg-[#f1efe8] px-3 py-2 text-sm text-[#4b4f55]">
            Next.js + LangGraph monorepo
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-4 px-5 py-5 lg:grid-cols-[360px_1fr_360px]">
        <section className="rounded-md border border-[#d8d3c6] bg-white p-4">
          <div className="mb-4">
            <h2 className="text-base font-semibold">Product Description</h2>
            <p className="mt-1 text-sm text-[#69707a]">
              제품이나 기술 흐름을 입력하면 Agent가 검색, 청구항 분해, 매칭, 리포트 생성을 진행합니다.
            </p>
          </div>
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="min-h-72 w-full resize-none rounded-md border border-[#c9c3b4] bg-[#fbfaf7] p-3 text-sm leading-6 outline-none focus:border-[#3066be]"
            placeholder="예: 사용자가 질문을 입력하면 내부 문서를 검색하고, 검색 결과를 기반으로 답변과 출처를 제공하는 AI 문서 분석 서비스..."
          />
          <button
            type="button"
            onClick={seedDemoEvents}
            className="mt-3 h-10 w-full rounded-md bg-[#204e4a] px-4 text-sm font-semibold text-white hover:bg-[#183f3b]"
          >
            Preview Agent Flow
          </button>
        </section>

        <section className="rounded-md border border-[#d8d3c6] bg-white">
          <div className="border-b border-[#e5e0d4] p-4">
            <h2 className="text-base font-semibold">Agent Timeline</h2>
            <p className="mt-1 text-sm text-[#69707a]">
              SSE 이벤트가 연결되면 각 단계와 tool call 결과가 실시간으로 쌓입니다.
            </p>
          </div>
          <div className="grid gap-3 p-4">
            {steps.map((step) => {
              const done = completedSteps.has(step.id);
              return (
                <div
                  key={step.id}
                  className="flex items-center gap-3 rounded-md border border-[#e5e0d4] bg-[#fbfaf7] p-3"
                >
                  <span
                    className={[
                      "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold",
                      done ? "bg-[#204e4a] text-white" : "bg-[#e7e2d5] text-[#5d6470]",
                    ].join(" ")}
                  >
                    {done ? "✓" : "·"}
                  </span>
                  <div>
                    <p className="text-sm font-semibold">{step.label}</p>
                    <p className="text-xs text-[#69707a]">
                      {done ? "Completed" : "Waiting for agent event"}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="border-t border-[#e5e0d4] p-4">
            <h3 className="mb-3 text-sm font-semibold">Event Stream</h3>
            <div className="max-h-72 overflow-auto rounded-md bg-[#20242a] p-3 font-mono text-xs text-[#e9edf2]">
              {events.length === 0 ? (
                <p className="text-[#aab2bd]">No agent events yet.</p>
              ) : (
                events.map((event, index) => (
                  <pre key={`${event.type}-${index}`} className="mb-2 whitespace-pre-wrap">
                    {JSON.stringify(event, null, 2)}
                  </pre>
                ))
              )}
            </div>
          </div>
        </section>

        <aside className="grid gap-4">
          <section className="rounded-md border border-[#d8d3c6] bg-white p-4">
            <h2 className="text-base font-semibold">Evidence Panel</h2>
            <p className="mt-1 text-sm text-[#69707a]">
              특허 후보, 청구항 원문, 매칭 근거를 보여줄 영역입니다.
            </p>
            <div className="mt-4 rounded-md border border-[#e5e0d4] bg-[#fbfaf7] p-3 text-sm">
              <p className="font-semibold">Primary focus</p>
              <p className="mt-1 text-[#69707a]">Independent claims and technical feature overlap.</p>
            </div>
          </section>

          <section className="rounded-md border border-[#d8d3c6] bg-white p-4">
            <h2 className="text-base font-semibold">Claim Chart</h2>
            <div className="mt-3 grid gap-2">
              {chartRows.length === 0 ? (
                <p className="rounded-md border border-dashed border-[#c9c3b4] p-3 text-sm text-[#69707a]">
                  분석이 시작되면 청구항 구성요소와 제품 기능 매칭 결과가 표시됩니다.
                </p>
              ) : (
                chartRows.map((row, index) => (
                  <div key={index} className="rounded-md border border-[#e5e0d4] p-3 text-sm">
                    <p className="font-semibold">{String(row.data?.claimElement)}</p>
                    <p className="mt-1 text-[#69707a]">{String(row.data?.productFeature)}</p>
                    <span className="mt-2 inline-flex rounded bg-[#e4eef4] px-2 py-1 text-xs font-semibold text-[#25506b]">
                      {String(row.data?.match)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="rounded-md border border-[#d8d3c6] bg-white p-4">
            <h2 className="text-base font-semibold">Draft Report</h2>
            <p className="mt-3 whitespace-pre-wrap rounded-md bg-[#fbfaf7] p-3 text-sm text-[#4b4f55]">
              {String(report?.data?.markdown ?? "No report generated yet.")}
            </p>
          </section>
        </aside>
      </div>
    </main>
  );
}
