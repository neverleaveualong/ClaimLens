# KIPRIS 청구항 수집기

## 목적

Phase 2의 목표는 KIPRIS Open API에서 특허 후보와 청구항 원문을 가져와 PostgreSQL에 저장하는 것이다.

현재 구현은 public API endpoint가 아니라 백엔드 내부 수집 스크립트다. 이후 Agent workflow에서 `Search Agent`와 `Claim Agent`가 이 수집 로직을 tool처럼 호출하는 구조로 확장한다.

## 실행 흐름

```text
검색어 입력
-> KIPRIS getWordSearch 호출
-> applicationNumber 확보
-> patentClaimInfo 호출
-> 청구항 원문 파싱
-> Patent / Claim / ClaimElement 저장
```

출원번호를 직접 넣는 경우:

```text
applicationNumber 입력
-> patentClaimInfo 호출
-> 청구항 원문 파싱
-> Patent / Claim / ClaimElement 저장
```

## 추가된 코드

```text
apps/api/app/clients/kipris.py
```

KIPRIS XML API 호출을 담당한다.

- `getWordSearch`: 키워드 기반 특허 후보 검색
- `patentClaimInfo`: 출원번호 기반 청구항 조회

```text
apps/api/app/services/claim_parser.py
```

청구항 원문을 DB 저장용 구조로 바꾼다.

- 청구항 번호 추출
- HTML/XML 태그 제거
- `삭제` 청구항 판별
- 독립항/종속항 추정
- 청구항 구성요소 분리

```text
apps/api/app/services/kipris_collector.py
```

KIPRIS 응답을 PostgreSQL에 저장한다.

- `Patent` upsert
- `Claim` upsert
- `ClaimElement` 재생성
- 같은 출원번호를 다시 수집해도 중복 저장하지 않음

```text
apps/api/app/scripts/collect_kipris.py
```

로컬 실행용 CLI다.

## 실행 예시

```bash
cd apps/api
python -m app.scripts.collect_kipris --application-number 1020060033658
```

```bash
cd apps/api
python -m app.scripts.collect_kipris --keyword "문서검색" --limit 1
```

## 검증 결과

테스트 출원번호:

```text
1020060033658
```

저장 결과:

```text
claims=11
active=8
deleted=3
```

검색어 `문서검색`, limit 1 기준 저장 결과:

```text
applicationNumber=1020240134264
claims=10
active=10
deleted=0
```

PostgreSQL 검증 결과:

```text
patents=2
claims=21
claim_elements=43
```

## 현재 한계

- 출원번호만 직접 입력하는 경우 서지 상세 API를 호출하지 않으므로 제목은 임시값으로 저장된다.
- `ClaimElement` 분리는 rule-based MVP라서 법률적으로 완전한 claim chart 수준은 아니다.
- 다음 단계에서 `Claim Agent`가 독립항 중심으로 분석할 수 있도록 parser 보강이 필요하다.

