# ClaimLens Development Roadmap

## 목표

ClaimLens는 단순 특허 검색 서비스가 아니라, KIPRIS 특허/청구항 데이터를 기반으로 제품 기능과 특허 청구항을 비교해 claim chart와 기술 검토 초안을 생성하는 Multi-Agent Patent Analysis System이다.

개발은 한 번에 멀티에이전트를 완성하는 방식이 아니라, 데이터 저장 기반을 먼저 만든 뒤 V1 workflow, V2 supervisor multi-agent, V3 reflection loop로 단계적으로 확장한다.

## Phase 0. Foundation

목표:

- 개발 환경과 기본 API 구조를 정리한다.
- 이후 DB, collector, agent workflow가 들어갈 위치를 확정한다.

작업:

- ClaimLens `.env` 정리
- FastAPI 설정 확인
- PostgreSQL 연결 설정 추가
- SQLAlchemy 또는 SQLModel 선택
- Alembic migration 구조 추가
- 기본 health check 유지

산출물:

- DB 연결 가능한 FastAPI backend
- migration 실행 구조
- 환경변수 문서

완료 기준:

- backend가 실행된다.
- DB connection test가 통과한다.
- migration command가 동작한다.

## Phase 1. PostgreSQL Schema

목표:

- KIPRIS 원본 데이터와 ClaimLens 분석 데이터를 저장할 DB 구조를 만든다.

우선 테이블:

- `patents`
- `claims`
- `claim_elements`

후속 테이블:

- `analysis_runs`
- `analysis_events`
- `claim_charts`

작업:

- patents 모델/테이블 작성
- claims 모델/테이블 작성
- claim_elements 모델/테이블 작성
- unique constraint 설정
  - patents.application_number
  - claims.patent_id + claims.claim_number
- index 설정
  - application_number
  - ipc_number
  - is_independent
  - status
- migration 생성

산출물:

- DB schema
- migration file
- schema visual 문서와 일치하는 테이블 구조

완료 기준:

- migration으로 테이블이 생성된다.
- 테스트 데이터 insert/select가 가능하다.

## Phase 2. KIPRIS Collector

목표:

- KIPRIS API에서 특허 후보와 청구항을 가져와 PostgreSQL에 저장한다.

핵심 흐름:

```text
keyword
-> getAdvancedSearch 또는 getWordSearch
-> applicationNumber 확보
-> patentClaimInfo
-> claimInfo[].claim 추출
-> normalize
-> patents / claims upsert
```

작업:

- KIPRIS client 작성
- keyword search 함수 작성
- patentClaimInfo 함수 작성
- claim number 파싱
- 삭제 청구항 탐지
- 독립항/종속항 rule-based 판별
- raw_text / normalized_text 저장
- collector script 작성

추천 명령:

```text
python -m app.scripts.collect_kipris --keyword "문서검색" --limit 10
```

산출물:

- KIPRIS collector
- 10건 seed 저장 결과
- 청구항 저장 로그

완료 기준:

- 검색어 1개로 특허 10건을 수집한다.
- 각 특허의 청구항이 claims 테이블에 저장된다.
- 삭제 청구항은 status=deleted로 저장된다.
- 독립항이 is_independent=true로 구분된다.

## Phase 3. Claim Parsing

목표:

- 청구항 원문을 Agent가 비교 가능한 claim element 단위로 분해한다.

작업:

- 독립항만 우선 선택
- rule-based pre-split 구현
- LLM-assisted parsing 옵션 추가
- parser_confidence 저장
- source_span 저장
- claim_elements upsert

우선 rule:

- 세미콜론 기준 분리
- `포함하는`, `수단`, `모듈`, `단계` 기준 보조 분리
- `제 1 항에 있어서`는 종속항으로 분류
- `삭제` 청구항 제외

산출물:

- claim parser
- claim_elements 데이터
- parser unit tests

완료 기준:

- 독립항 1개가 3-12개 구성요소로 분해된다.
- 빈 element가 저장되지 않는다.
- 원문에 없는 요소가 생성되지 않는다.

## Phase 4. Pinecone / Vector Search

목표:

- PostgreSQL에 저장된 특허/청구항을 의미 검색할 수 있게 만든다.

역할 분리:

```text
PostgreSQL = 원문과 정형 데이터
Pinecone = 의미 검색용 벡터
```

작업:

- OpenAI embedding client 추가
- abstract embedding 생성
- independent claim embedding 생성
- claim element embedding 생성
- Pinecone metadata 설계
- patent_id / claim_id / claim_element_id 매핑
- search API 내부 함수 작성

산출물:

- Pinecone index
- embedding ingestion script
- semantic search function

완료 기준:

- 제품 설명을 embedding해 관련 특허/청구항 top-k를 찾는다.
- Pinecone 결과 id로 PostgreSQL 원문을 조회할 수 있다.

## Phase 5. V1 Agent Workflow

목표:

- 순차 workflow로 claim chart 생성까지 먼저 완성한다.

흐름:

```text
Input Analyzer
-> Search
-> Claim Loader
-> Parser
-> Matcher
-> Validator
-> Report
```

작업:

- 제품 기능 추출
- 후보 특허 검색
- claim_elements 로드
- claim element vs product feature 비교
- match_status 제한
  - matched
  - partial
  - not_found
  - uncertain
- evidence 필수화
- claim_charts 저장
- final report 생성

산출물:

- V1 LangGraph workflow
- SSE event stream
- claim chart output

완료 기준:

- 제품 설명 1개를 입력하면 claim chart가 생성된다.
- 근거 없는 matched가 나오지 않는다.
- 최종 리포트가 claim chart 범위를 벗어나지 않는다.

## Phase 6. V2 Supervisor Multi-Agent

목표:

- V1 workflow를 Supervisor + Specialist Agents 구조로 확장한다.

Agent 역할:

- Supervisor Agent
- Search Agent
- Claim Agent
- Parsing Agent
- Matching Agent
- Validation Agent
- Report Agent

작업:

- Agent별 input/output contract 정의
- Supervisor state 정의
- retry_count 관리
- fallback 상태 정의
- agent decision SSE event 추가
- tool call log 저장

Supervisor 판단:

```text
candidate_count 부족 -> Search Agent 재실행
claim missing -> Claim Agent 보강
parser_confidence 낮음 -> Parsing Agent 재실행
evidence 부족 -> Matching Agent 재실행 또는 uncertain downgrade
report unsupported -> Report Agent 재작성
```

산출물:

- Multi-agent graph
- Supervisor decision logs
- agent별 테스트

완료 기준:

- Supervisor가 최소 2개 이상의 분기 결정을 수행한다.
- Agent별 결과가 analysis_events에 저장된다.
- SSE에서 어떤 Agent가 왜 실행됐는지 보인다.

## Phase 7. V3 Reflection And Recovery

목표:

- Validation 결과를 기반으로 재계획과 실패 복구 루프를 추가한다.

Reflection 예시:

```text
Validation Agent: evidence_missing
-> Supervisor: Search Agent 재실행 결정
-> Search Agent: query rewrite
-> Claim Agent: missing claims fetch
-> Matching Agent: comparison retry
-> Validation Agent: pass or downgrade
```

작업:

- reflection reason enum 작성
- bounded retry limit 설정
- query rewrite prompt 작성
- evidence quality score 작성
- downgrade policy 작성
- loop termination 조건 작성

산출물:

- reflection loop
- fallback demo case
- interview-ready demo scenario

완료 기준:

- 근거 부족 상황에서 재검색 또는 재매칭이 발생한다.
- 재시도 후에도 약하면 uncertain으로 낮춘다.
- 무한 루프가 발생하지 않는다.

## Phase 8. Frontend Portfolio UI

목표:

- Agent 분석 과정을 사용자에게 보이는 포트폴리오 UI로 만든다.

화면:

- 제품 설명 입력
- Agent timeline
- Supervisor decision panel
- 후보 특허 목록
- 청구항 preview
- claim chart table
- final report

작업:

- SSE EventSource 연결
- timeline 렌더링
- claim chart row stream 반영
- fallback/uncertain 상태 표시
- export 버튼 또는 markdown preview

산출물:

- Next.js analysis workspace
- 데모 가능한 UI

완료 기준:

- 분석 진행 상황이 실시간으로 보인다.
- claim chart가 표로 보인다.
- Supervisor decision이 UI에 표시된다.

## Phase 9. Quality And Portfolio Packaging

목표:

- 면접과 포트폴리오에서 설명 가능한 수준으로 안정화한다.

작업:

- backend unit tests
- collector integration test
- parser tests
- matcher output validation tests
- frontend smoke test
- README 작성
- architecture diagram 정리
- demo seed dataset 고정
- 발표용 시나리오 2-3개 작성

산출물:

- README
- demo screenshots
- architecture docs
- interview notes

완료 기준:

- 로컬에서 재현 가능한 데모가 있다.
- README만 보고 실행 흐름을 이해할 수 있다.
- 면접용 질문에 답할 근거 문서가 있다.

## 추천 구현 순서 요약

```text
1. DB 연결 + schema
2. KIPRIS collector
3. claims 저장/정규화
4. claim_elements 파싱
5. Pinecone embedding
6. V1 LangGraph
7. V2 Supervisor multi-agent
8. V3 reflection loop
9. Frontend demo
```

가장 중요한 첫 목표:

```text
KIPRIS patentClaimInfo 응답을 PostgreSQL claims 테이블에 안정적으로 저장한다.
```
