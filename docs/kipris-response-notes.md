# KIPRIS Response Notes

## 확인 일자

2026-06-07

TechDocs backend `.env`의 `KIPRIS_API_KEY`를 사용해 KIPRIS Plus 응답을 샘플 확인했다. API 키 값은 저장하지 않는다.

## 테스트한 API

Base URL:

```text
http://plus.kipris.or.kr/kipo-api/kipi
```

테스트한 endpoint:

```text
patUtiModInfoSearchSevice/getAdvancedSearch
patUtiModInfoSearchSevice/getBibliographyDetailInfoSearch
patUtiModInfoSearchSevice/getAnnFullTextInfoSearch
patUtiModInfoSearchSevice/getPubFullTextInfoSearch
patUtiModInfoSearchSevice/patentClaimInfo
```

공식 KIPRIS Plus 페이지의 Patent-Utility Model Publications 목록에는 `getAdvancedSearch`, `getBibliographyDetailInfoSearch`, `patentClaimInfo`, `getPubFullTextInfoSearch`, `getAnnFullTextInfoSearch`가 포함되어 있다.

## 핵심 발견

### 1. 검색 API는 후보 식별에 충분하다

`getAdvancedSearch`에서 다음 필드가 확인됐다.

```text
applicationNumber
registerNumber
inventionTitle
applicantName
ipcNumber
applicationDate
registerStatus
astrtCont
```

예시 검색어 `문서 검색` 기준으로 관련 특허가 정상 반환됐다.

ClaimLens에서 검색 API의 역할:

```text
후보 특허 검색
-> applicationNumber 확보
-> title/abstract/applicant/ipc 기반 후보 ranking
-> 상세 조회로 청구항 확보
```

### 2. 청구항은 상세 조회 응답에 직접 들어온다

중요한 발견:

`getBibliographyDetailInfoSearch` 응답 안에 아래 구조로 청구항 원문이 들어온다.

```text
response.body.item.claimInfoArray.claimInfo[].claim
```

따라서 MVP의 청구항 수집 1순위는 별도 PDF 추출이 아니라 `getBibliographyDetailInfoSearch`가 맞다.

샘플:

```text
applicationNumber: 10-2024-0134264
claimCount: 10
parsed claimInfo items: 10
```

```text
applicationNumber: 10-1996-0002386
claimCount: 22
parsed claimInfo items: 22
```

### 3. claimCount와 실제 claimInfo item 수가 다를 수 있다

샘플 `10-2006-0033658`에서는 다음 차이가 있었다.

```text
claimCount: 8
parsed claimInfo items: 11
```

원인:

- 삭제 청구항이 `2. 삭제`, `8. 삭제`, `10. 삭제` 형태로 포함됨
- 실제 claimInfo item 수는 삭제 항목까지 포함할 수 있음

설계 반영:

- `claimCount`를 절대 기준으로 쓰지 않는다.
- `claimInfoArray.claimInfo[]`를 실제 claim row 기준으로 저장한다.
- `삭제` 청구항은 `status = deleted`로 저장하고 분석 대상에서는 제외한다.

### 4. 오래된 특허는 HTML 태그가 섞일 수 있다

샘플 `10-1996-0002386` 청구항에는 다음 형태의 태그가 섞였다.

```text
<P INDENT="14" ALIGN="JUSTIFIED">...</P>
```

설계 반영:

- `raw_text`는 원본 그대로 저장한다.
- `normalized_text`에서는 XML/HTML tag를 제거한다.
- 줄바꿈, 공백, 문단 태그 제거 후 claim number를 보존한다.

### 5. 독립항 판별은 rule-based로 가능하다

샘플 기준으로 종속항은 다음 표현을 포함한다.

```text
제 1 항에 있어서
제 1 항 내지 제 5 항 중 어느 한 항에 있어서
제 8 항에 있어서
```

독립항 후보는 다른 청구항을 참조하지 않는다.

샘플 독립항 후보:

```text
10-2024-0134264: 1번, 10번
10-2006-0033658: 1번, 7번
10-1996-0002386: 1번, 8번, 16번
```

설계 반영:

- MVP는 독립항만 claim chart 대상으로 삼는다.
- 다른 청구항 참조 문구가 있으면 종속항으로 분류한다.
- `삭제`는 분석 제외.
- 독립항 후보가 여러 개면 claim number 순서로 최대 3개만 분석한다.

### 6. 등록/공개 전문 API는 보조 경로다

`getAnnFullTextInfoSearch`는 등록 전문 PDF 경로를 반환했다.

```text
docName: 1020240134264.pdf
path: fileToss.jsp?... 
```

`getPubFullTextInfoSearch`는 해당 샘플에서 빈 item을 반환했다.

설계 반영:

- 전문 PDF는 청구항 원문 확보의 1순위가 아니다.
- `getBibliographyDetailInfoSearch`에 claimInfoArray가 없을 때만 보조 경로로 둔다.
- PDF 텍스트 추출은 별도 dependency가 필요하므로 MVP에서는 후순위로 둔다.

### 7. patentClaimInfo는 청구항 전용 API로 사용 가능

2026-06-08 재테스트에서 `patentClaimInfo` endpoint가 정상 응답을 반환하는 것을 확인했다.

테스트 조건:

```text
endpoint: patUtiModInfoSearchSevice/patentClaimInfo
parameter: applicationNumber=1020060033658
auth parameter: accessKey
resultCode: 00
resultMsg: success
parsed claimInfo items: 11
```

응답 구조:

```text
response.body.items.claimInfo[].claim
```

설계 반영:

- 청구항 수집 1순위는 `patentClaimInfo`로 둔다.
- `getBibliographyDetailInfoSearch`는 서지 상세와 청구항을 함께 확인하는 fallback 또는 보강 경로로 둔다.
- `patentClaimInfo` 응답에도 삭제 청구항이 포함될 수 있으므로 `삭제` 항목은 저장하되 분석 대상에서 제외한다.

## ClaimLens 청구항 수집 우선순위

최신 설계 기준:

```text
1. patentClaimInfo
   - items.claimInfo[].claim 사용
   - 청구항 전용 API

2. getBibliographyDetailInfoSearch
   - claimInfoArray.claimInfo[].claim 사용
   - 서지 상세 fallback 및 보강 경로

3. getAnnFullTextInfoSearch
   - 등록 전문 PDF path 확보
   - 상세 응답에 청구항이 없을 때만 보조

4. getPubFullTextInfoSearch
   - 공개 전문 PDF path 확보
   - 공개 특허에서 필요할 때 보조
```

## Workflow 반영

기존 가정:

```text
검색 API -> 별도 청구항 API -> 청구항 분석
```

수정된 workflow:

```text
1. getAdvancedSearch로 후보 검색
2. applicationNumber 기준 patentClaimInfo 호출
3. items.claimInfo[].claim에서 청구항 원문 추출
4. raw_text / normalized_text 저장
5. 삭제 청구항 제외
6. 독립항 판별
7. 독립항 claim element 분해
8. Feature Matcher가 제품 기능과 비교
```

## DB 설계 반영

`claims` table에 필요한 필드:

```text
id
patent_id
claim_number
raw_text
normalized_text
status: active | deleted | unavailable
is_independent
dependency_claim_numbers
source_endpoint: getBibliographyDetailInfoSearch
source_document_type: bibliography_detail
parser_confidence
created_at
updated_at
```

`patents` table에 필요한 필드:

```text
application_number
application_number_normalized
register_number
publication_number
title
title_eng
abstract
applicant_name
application_date
register_status
claim_count_reported
claim_items_count
last_fetched_at
fetch_status
```

## 아키텍처 결론

KIPRIS는 실시간 검색/분석 API라기보다 원천 데이터 공급원으로 사용한다.

다만 청구항 원문이 상세 응답에서 직접 제공되므로, ClaimLens MVP는 PDF 파싱 없이도 claim chart 생성이 가능하다.

가장 현실적인 MVP 흐름:

```text
KIPRIS getAdvancedSearch
-> patentClaimInfo
-> claimInfo 추출
-> local DB seed 저장
-> 독립항 중심 claim chart 생성
```

이 결과로 ClaimLens의 초기 구현은 `KIPRIS PDF 전문 파싱`보다 `patentClaimInfo 청구항 정규화`에 집중해야 한다.
