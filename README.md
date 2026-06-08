# ClaimLens

ClaimLens는 제품/기술 설명과 특허 청구항을 비교해 claim chart와 기술 검토 초안을 생성하는 AI Agent 포트폴리오 프로젝트입니다.

이 프로젝트는 단순 특허 검색 서비스가 아니라, KIPRIS 특허/청구항 데이터와 Agentic workflow를 연결하는 것을 목표로 합니다.

1. 제품 또는 기술 설명을 분석합니다.
2. 저장된 KIPRIS 데이터에서 관련 특허 후보를 검색합니다.
3. 독립항을 claim element 단위로 분해합니다.
4. 제품 기능과 청구항 구성요소를 비교합니다.
5. 근거 기반 claim chart와 기술 검토 리포트를 생성합니다.

ClaimLens는 법률적 침해 판단을 제공하지 않습니다. 근거, 불확실성, 추적 가능한 분석 단계를 포함한 기술 검토 초안을 제공하는 것을 목표로 합니다.

## 개발 방향

현재 개발 방향은 다음 순서로 진행합니다.

```text
Phase 0: FastAPI + PostgreSQL 연결 기반
Phase 1: patents / claims / claim_elements 스키마
Phase 2: KIPRIS collector
Phase 3: 청구항 구성요소 분해
Phase 4: Pinecone 기반 의미 검색
Phase 5: V1 순차 Agent workflow
Phase 6: Supervisor + Specialist Agents
Phase 7: Reflection / Recovery loop
```

최종 포지셔닝은 `Multi-Agent Patent Analysis System`입니다.

## Monorepo

```text
apps/
  web/     Next.js frontend for agent workflow UI
  api/     FastAPI + LangGraph backend
packages/
  shared/  Shared TypeScript contracts for frontend events
docs/
  project-plan.md
  development-roadmap.md
  *.html
```

## 로컬 개발

로컬 PostgreSQL:

```bash
docker compose up -d postgres
```

Frontend:

```bash
npm run dev:web
```

Backend:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

DB 연결 확인:

```bash
curl http://localhost:8000/health/db
```
