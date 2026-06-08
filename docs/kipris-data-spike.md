# KIPRIS Data Spike Plan

## 목적

ClaimLens의 아키텍처를 추상 설계로만 정하지 않고, 실제 KIPRIS 응답 형태를 확인한 뒤 workflow와 DB schema를 조정한다.

이 spike의 목표는 "KIPRIS 연동 완성"이 아니라 다음 질문에 답하는 것이다.

1. 검색 API 응답에서 후보 특허를 안정적으로 식별할 수 있는가?
2. 출원번호/공개번호/등록번호 중 어떤 번호를 claim fetch key로 써야 하는가?
3. 청구항 원문은 어떤 API/필드에서 가장 안정적으로 가져올 수 있는가?
4. 독립항/종속항을 rule-based로 구분할 수 있는가?
5. 실제 청구항 텍스트를 claim element로 분해할 때 어떤 전처리가 필요한가?

## 현재 확인한 공식 표면

KIPRIS Plus 특허/실용 서비스에는 다음 계열이 있다.

- `getWordSearch`: 키워드 기반 검색
- `getBibliographyDetailInfoSearch`: 서지 상세 조회
- `patentClaimInfo`: 서지 계열의 청구항 정보
- `getPubFullTextInfoSearch`: 공개 전문 조회
- `getAnnFullTextInfoSearch`: 등록 전문 조회
- `getRevisionFullTextInfoSearch`: 보정 전문 조회

## 2026-06-07 샘플 확인 결과

TechDocs backend `.env`의 `KIPRIS_API_KEY`를 사용해 실제 응답을 확인했다.

결론:

- `getAdvancedSearch`는 후보 특허 검색과 `applicationNumber` 확보에 충분하다.
- `getBibliographyDetailInfoSearch` 응답에 `claimInfoArray.claimInfo[].claim` 형태로 청구항 원문이 직접 들어온다.
- `getAnnFullTextInfoSearch`는 등록 전문 PDF path를 반환하지만, MVP 청구항 수집 1순위는 아니다.
- `getPubFullTextInfoSearch`는 샘플에서 빈 item을 반환했다.
- `patentClaimInfo`는 공식 목록에는 있으나 현재 테스트한 파라미터 조합에서는 `INVALID_REQUEST_PARAMETER_ERROR`가 반환됐다.

따라서 ClaimLens MVP의 청구항 수집 1순위는 `getBibliographyDetailInfoSearch`로 확정한다.

자세한 응답 분석은 `docs/kipris-response-notes.md`에 정리했다.

Open API는 월 1,000회 호출까지 무료 제공된다. 따라서 개발 초반에는 호출 횟수를 아끼기 위해 seed dataset을 먼저 만들고, live fetch는 보강 용도로 제한한다.

## Spike 순서

### 1. API 키 준비

`.env` 또는 `apps/api/.env`에 다음 값을 둔다.

```text
KIPRIS_API_KEY=...
```

키 값은 코드나 문서에 저장하지 않는다.

### 2. 키워드 검색 응답 샘플 확보

대상 질의:

```text
RAG 문서 검색
질의응답 시스템
문서 검색 답변 생성
AI 검색 추천
OCR 문서 처리
```

확인할 필드:

```text
application_number
publication_number
registration_number
title
abstract
applicant
filing_date
ipc
cpc
source_url
```

결정할 것:

- 후보 특허 식별자는 무엇으로 둘지
- 검색 결과에 claim fetch에 필요한 번호가 충분히 있는지
- local DB 저장 전 필드명이 어떻게 normalize되어야 하는지

### 3. 상세/청구항 조회 샘플 확보

검색 결과에서 5-10개 특허를 골라 다음 순서로 조회한다.

```text
1. getBibliographyDetailInfoSearch
2. getAnnFullTextInfoSearch
3. getPubFullTextInfoSearch
4. patentClaimInfo
```

확인할 것:

- 청구항 원문이 어느 응답에서 가장 안정적으로 나오는지
- 청구항 번호가 필드로 분리되어 있는지
- 청구항 전체가 하나의 문자열로 오는지
- XML/HTML artifact가 섞이는지
- 공개 전문과 등록 전문의 청구항이 다를 때 어떤 것을 우선할지

우선순위 가정:

```text
1순위: getBibliographyDetailInfoSearch의 claimInfoArray
2순위: 등록/공개 전문 PDF path에서 청구항 영역을 추출하는 경우
3순위: patentClaimInfo는 파라미터 contract 확인 후 선택적 사용
4순위: 청구항 변동/보정 데이터는 보조 정보로만 사용
```

### 4. 청구항 정규화 실험

실제 claim text를 10개 정도 모아 다음 처리를 테스트한다.

```text
raw claim text
-> XML/HTML artifact 제거
-> 공백/줄바꿈 정리
-> 청구항 번호 정규화
-> 독립항/종속항 판별
-> claim element pre-split
```

독립항 판별 rule:

```text
종속항 후보:
  "제1항에 있어서"
  "청구항 1에 있어서"
  "제1항 또는 제2항에 있어서"
  "the method of claim 1"
  "according to claim 1"

독립항 후보:
  다른 청구항 참조가 없음
```

### 5. Feature Matcher 실험

하나의 demo product description과 실제 청구항 1개를 골라 claim chart를 수동/반자동으로 만든다.

확인할 것:

- claim element가 너무 잘게 쪼개지는지
- 제품 기능 추출 결과가 claim element와 비교 가능한 단위인지
- `matched`, `partial`, `not_found`, `uncertain` 기준이 실제 예시에서 구분되는지
- evidence 없이 matched가 나오는지

## Spike 산출물

```text
data/kipris_samples/search_results/*.json
data/kipris_samples/detail_results/*.json
data/kipris_samples/claims/*.json
docs/kipris-response-notes.md
docs/demo-claim-chart-example.md
```

민감한 API 키는 저장하지 않는다.

## Spike 이후 아키텍처 결정

Spike 결과로 다음을 확정한다.

1. `patents` table 필드
2. `claims` table 필드
3. claim fetch key 우선순위
4. 청구항 source 우선순위
5. 독립항 탐지 rule
6. claim parser 전처리 rule
7. live KIPRIS fetch fallback 조건
8. MVP seed dataset 크기와 수집 방식

## 예상 workflow 반영

Spike 전 설계:

```text
KIPRIS 검색 -> 청구항 조회 -> 분석
```

Spike 후 목표 설계:

```text
KIPRIS sample 분석
-> 응답 필드 normalize 기준 확정
-> seed dataset 구축
-> local DB 우선 분석
-> claim 없는 후보만 live fetch
-> claim source와 fetch status를 UI에 노출
```

이렇게 해야 면접에서 "외부 API를 붙였다"가 아니라 "실제 데이터 응답을 분석하고, 그 제약에 맞춰 workflow와 fallback을 설계했다"고 설명할 수 있다.
