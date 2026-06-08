# ClaimLens 면접 설명 노트

## 한 줄 소개

ClaimLens는 제품/기술 설명과 특허 청구항을 비교해, 청구항 구성요소별 기술적 유사성을 claim chart 형태로 정리해주는 AI Agent 프로젝트입니다.

법률적인 침해 판단을 내리는 서비스가 아니라, 특허 문서를 기술적으로 검토하기 위한 1차 분석 초안을 만드는 도구입니다.

## 왜 만들었는가

기존 RAG 챗봇은 관련 문서를 찾아 답변하는 데는 강하지만, 특허 분석처럼 구조화된 비교가 필요한 문제에는 한계가 있습니다.

특허에서 중요한 부분은 초록이나 설명이 아니라 청구항입니다. 그래서 단순히 관련 특허를 검색하는 것이 아니라, 청구항을 구성요소로 분해하고 제품 기능과 하나씩 매핑하는 흐름으로 문제를 다시 정의했습니다.

## 해결하려는 문제

1. 특허 문서는 길고 검색 결과만으로 판단하기 어렵습니다.
2. 청구항은 한 문장 안에 여러 기술 구성요소가 들어 있어 직접 비교하기 어렵습니다.
3. LLM이 최종 결론을 바로 만들면 근거가 약하거나 과장될 수 있습니다.
4. 분석 시간이 길어지면 사용자는 백엔드가 무엇을 하는지 알기 어렵습니다.

## 핵심 해결 방식

- KIPRIS 기반 특허 데이터를 수집하고, 초록/청구항/메타데이터를 저장합니다.
- 제품 설명에서 주요 기능을 추출합니다.
- 독립항을 우선 선택하고 청구항 구성요소로 분해합니다.
- 각 구성요소와 제품 기능을 행 단위로 비교합니다.
- `matched`, `partial`, `not_found`, `uncertain` 상태로 결과를 제한합니다.
- 최종 보고서는 자유 생성하지 않고 claim chart 결과를 기반으로 생성합니다.
- LangGraph로 분석 단계를 명확히 나누고, SSE로 진행 상황을 프론트엔드에 스트리밍합니다.

## 기술적으로 강조할 점

### 단순 RAG와의 차이

단순 RAG는 관련 특허를 찾아 요약하는 데 그칠 수 있습니다. ClaimLens는 검색 이후에 청구항 파싱, 제품 기능 추출, 구성요소별 매칭, 근거 기반 보고서 생성까지 이어지는 구조화된 workflow를 갖습니다.

### Agent를 쓴 이유

분석 과정이 단일 프롬프트로 끝나지 않고, 검색-상세조회-청구항분해-비교-평가-보고서 생성으로 이어지는 상태 기반 작업입니다. 각 단계의 입력과 출력이 다음 단계에 영향을 주기 때문에 LangGraph로 상태를 관리하는 방식이 적합하다고 판단했습니다.

또한 단순히 정해진 순서대로 실행하는 파이프라인이 아니라, 검색 결과가 부족하면 query를 다시 만들고, local DB에 청구항이 없으면 KIPRIS fetch로 보강하고, 파싱 신뢰도가 낮으면 재시도하고, 근거 없는 매칭은 `uncertain`으로 낮추는 조건부 workflow로 설계했습니다.

### Tool calling을 쓰는 방식

이 프로젝트에서 tool calling은 외부 API 호출만 의미하지 않습니다. local DB 검색, vector search, KIPRIS fetch, 청구항 정규화, 독립항 탐지, claim element parsing, feature matching, claim chart validation 같은 내부 기능도 typed tool로 노출합니다.

각 tool call은 입력과 출력을 기록하고 SSE로 프론트엔드에 보여줍니다. 그래서 사용자는 Agent가 어떤 검색어를 만들었는지, 어떤 특허를 찾았는지, 왜 KIPRIS fetch를 했는지, 어떤 claim chart row가 검증에 실패했는지 확인할 수 있습니다.

### SSE를 쓴 이유

분석은 시간이 걸릴 수 있고, 사용자는 중간에 어떤 단계가 진행 중인지 알아야 합니다. WebSocket까지 필요한 양방향 통신은 아니기 때문에 SSE로 agent timeline, tool call, claim chart row를 순차적으로 스트리밍하도록 설계했습니다.

### 환각을 줄이는 방식

최종 답변을 바로 생성하지 않고 claim chart를 먼저 만듭니다. 각 행에는 청구항 구성요소, 매칭된 제품 기능, 상태, 근거, 불확실성을 기록합니다. 최종 보고서는 이 구조화된 결과를 요약하게 해서 근거 없는 결론 생성을 줄입니다.

### Local DB와 KIPRIS fetch 기준

KIPRIS는 원천 데이터 공급원으로 보고, 실제 분석은 local DB에 저장된 seed dataset을 우선 사용합니다. 외부 API에 매번 의존하면 속도, 호출 제한, 데이터 누락 때문에 데모 안정성이 떨어질 수 있기 때문입니다.

기본 흐름은 local PostgreSQL과 vector search로 후보 특허를 먼저 찾고, 청구항이 없거나 사용자가 refresh를 요청하거나 후보가 부족할 때만 KIPRIS live fetch를 수행합니다. KIPRIS fetch가 실패해도 전체 분석을 중단하지 않고, 가능한 후보로 계속 진행하면서 `claim_unavailable` 또는 `fetch_failed` 상태를 UI에 표시합니다.

### 청구항 추출 방식

검색 API로 바로 검토표를 만드는 것이 아니라, 먼저 출원번호/공개번호/등록번호를 확보한 뒤 상세 또는 공보 데이터에서 청구항 원문을 가져옵니다. 가져온 청구항은 raw text와 normalized text를 함께 저장하고, MVP에서는 독립항을 우선 분석합니다.

독립항 여부는 소스에서 제공하는 dependency 정보가 있으면 그것을 우선 사용하고, 없으면 "제1항에 있어서", "the method of claim 1"처럼 다른 청구항을 참조하는 표현을 기준으로 종속항을 판단합니다.

실제 KIPRIS 샘플을 확인해보니 `getBibliographyDetailInfoSearch` 응답 안에 `claimInfoArray.claimInfo[].claim` 형태로 청구항 원문이 들어왔습니다. 그래서 MVP에서는 PDF 전문 파싱이나 별도 청구항 API보다 이 상세 조회 응답을 1순위로 사용하도록 설계했습니다.

또한 일부 특허는 `claimCount`와 실제 `claimInfo` 항목 수가 다르고, `2. 삭제` 같은 삭제 청구항도 응답에 포함됐습니다. 그래서 `claimCount`만 믿지 않고 실제 claim item을 기준으로 저장하되, 삭제 청구항은 보존만 하고 분석 대상에서는 제외하도록 설계했습니다.

### Feature Matcher 방식

Feature Matcher는 침해 여부를 판단하지 않고, 제품 기능과 청구항 구성요소의 기술적 매칭 정도만 비교합니다. 각 청구항 구성요소마다 관련 제품 기능 후보를 찾고, `matched`, `partial`, `not_found`, `uncertain` 중 하나로만 분류합니다.

`matched`와 `partial`은 반드시 제품 설명에서 근거가 있어야 하고, 근거가 없으면 `not_found`나 `uncertain`으로 처리합니다. 최종 리포트는 이 claim chart 행들을 요약하도록 설계해 LLM이 없는 근거를 새로 만들어내지 않게 합니다.

## 면접에서 받을 수 있는 질문

### Q. 이게 그냥 RAG 챗봇과 뭐가 다른가요?

관련 문서를 찾아 답변하는 것이 아니라, 특허 분석에서 중요한 청구항을 구성요소로 분해하고 제품 기능과 행 단위로 비교합니다. 즉 검색 결과를 답변으로 바로 쓰지 않고, claim chart라는 중간 산출물을 만든 뒤 최종 보고서를 생성합니다.

### Q. workflow가 그냥 정해진 순서대로 도는 파이프라인 아닌가요?

기본 단계는 검색, 청구항 조회, 파싱, 비교, 리포트 생성으로 정해져 있지만, 실행은 조건부로 분기합니다. 예를 들어 local 검색 결과가 부족하면 검색어를 재작성하거나 KIPRIS fetch를 수행하고, 청구항 파싱 신뢰도가 낮으면 한 번 재시도합니다. 또한 claim chart 검증에서 근거 없는 matched 결과가 나오면 다시 비교하거나 uncertain으로 낮춥니다. 그래서 단순 트리가 아니라 검증과 fallback이 있는 bounded agent workflow로 설계했습니다.

### Q. tool calling이 실제로 있나요?

있습니다. KIPRIS fetch 같은 외부 API뿐 아니라 local patent search, claim embedding search, claim normalization, independent claim detection, feature matching, claim chart validation도 tool로 정의합니다. 이렇게 해야 각 단계의 입력과 출력이 로그로 남고, SSE로 프론트에 표시되며, 테스트도 독립적으로 할 수 있습니다.

### Q. 왜 법률 판단이 아니라고 했나요?

특허 침해 여부는 법률적 판단과 전문가 검토가 필요한 영역입니다. 이 프로젝트는 침해 여부를 단정하지 않고, 기술 구성요소 간 유사성을 정리해 검토 초안을 제공하는 도구로 범위를 제한했습니다.

### Q. 가장 어려운 부분은 무엇인가요?

청구항을 안정적으로 구성요소로 나누고, LLM이 매칭 결과를 과장하지 않도록 제어하는 부분입니다. 이를 위해 match status를 제한하고, 각 결과에 evidence와 uncertainty를 포함하도록 설계했습니다.

### Q. 데이터가 부족하면 어떻게 하나요?

MVP에서는 50-100건 정도의 seed patent dataset을 먼저 구축하고, claim text가 없는 경우에는 claim chart를 생성하지 않도록 fallback을 둡니다. live KIPRIS fetch는 모든 분석에 의존하지 않고, 누락 데이터 보강이나 refresh 용도로만 사용합니다.

### Q. KIPRIS에서 청구항은 어떻게 가져오나요?

먼저 `getAdvancedSearch`로 후보 특허를 찾고 `applicationNumber`를 확보합니다. 그 다음 `getBibliographyDetailInfoSearch`를 호출하면 응답 안의 `claimInfoArray.claimInfo[].claim`에서 청구항 원문을 가져올 수 있었습니다. 이 값을 raw text로 저장하고, HTML 태그나 공백을 정리한 normalized text를 만들어 독립항 판별과 구성요소 분해에 사용합니다.

### Q. 왜 KIPRIS를 매번 직접 조회하지 않나요?

외부 API를 매번 호출하면 응답 속도, 호출 제한, 일시적 장애 때문에 분석 경험이 불안정해질 수 있습니다. 그래서 KIPRIS는 원천 데이터 수집과 누락 보강에 사용하고, 실제 분석은 local DB와 vector DB를 우선 사용하도록 설계했습니다.

### Q. Feature Matcher는 어떤 기준으로 판단하나요?

청구항 구성요소별로 제품 기능과 비교하고, 결과를 `matched`, `partial`, `not_found`, `uncertain` 네 가지로 제한합니다. 일치나 부분 일치로 판단하려면 반드시 제품 설명에서 근거가 있어야 하고, 근거가 부족하면 불확실하거나 찾을 수 없음으로 처리합니다.

### Q. 이 프로젝트로 어떤 역량을 보여주고 싶었나요?

AI API를 붙이는 능력보다, 복잡한 도메인 문제를 구조화하고 신뢰 가능한 분석 workflow로 설계하는 능력을 보여주고 싶었습니다. 특히 LangGraph 기반 agent 설계, SSE 스트리밍 UX, 근거 기반 claim chart, 불확실성 처리 방식을 강조할 수 있습니다.

## 포트폴리오에 넣을 핵심 문장

특허 분석에서 중요한 청구항을 구성요소로 분해하고, 제품 기능과 행 단위로 비교해 근거 기반 claim chart와 기술 검토 보고서를 생성하는 AI Agent를 구현했습니다. 단순 RAG 챗봇이 아니라 검색, 청구항 파싱, 기능 매칭, 불확실성 평가, SSE 기반 진행 상황 스트리밍을 포함한 구조화된 workflow로 설계했습니다.
