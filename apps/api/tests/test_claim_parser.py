from app.services.claim_parser import (
    ParsedClaimElement,
    normalize_application_number,
    parse_claim,
    parse_claims,
    select_independent_claims,
)


def test_parse_independent_claim_with_source_spans() -> None:
    claim = parse_claim(
        "1. 문서를 저장하는 저장수단; 사용자 질의를 입력받는 입력수단; "
        "질의와 관련된 문서를 검색하는 검색수단;"
    )

    assert claim is not None
    assert claim.claim_number == 1
    assert claim.status == "active"
    assert claim.is_independent is True
    assert claim.dependency_claim_numbers == []
    assert [element.text for element in claim.elements] == [
        "문서를 저장하는 저장수단",
        "사용자 질의를 입력받는 입력수단",
        "질의와 관련된 문서를 검색하는 검색수단",
    ]
    assert all(element.source_span in claim.normalized_text for element in claim.elements)
    assert claim.parser_confidence == 0.75
    assert claim.parser_method == "rule_based"
    assert claim.parser_status == "parsed"
    assert all(element.parser_method == "rule_based" for element in claim.elements)
    assert all(element.parser_status == "parsed" for element in claim.elements)


def test_parse_deleted_claim() -> None:
    claim = parse_claim("2. 삭제")

    assert claim is not None
    assert claim.claim_number == 2
    assert claim.status == "deleted"
    assert claim.is_independent is None
    assert claim.elements == []
    assert claim.parser_confidence == 0.95
    assert claim.parser_method == "rule_based"
    assert claim.parser_status == "skipped"


def test_parse_dependent_claim_with_html_tags() -> None:
    claim = parse_claim(
        '3. <P INDENT="14" ALIGN="JUSTIFIED">제 1 항에 있어서, '
        "상기 검색수단은 파일의 콘텐츠로부터 텍스트를 분류하는 시스템</P>"
    )

    assert claim is not None
    assert claim.claim_number == 3
    assert claim.status == "active"
    assert claim.is_independent is False
    assert claim.dependency_claim_numbers == [1]
    assert "<P" not in claim.normalized_text


def test_select_independent_claims_prefers_active_independent_claims() -> None:
    claims = parse_claims(
        [
            "1. 입력수단; 처리수단;",
            "2. 제 1 항에 있어서, 상기 처리수단은 검색수단을 포함하는 시스템",
            "3. 저장수단; 출력수단;",
            "4. 삭제",
        ]
    )

    selected = select_independent_claims(claims)

    assert [claim.claim_number for claim in selected] == [1, 3]


def test_llm_parser_is_used_when_rule_split_is_uncertain() -> None:
    claim = parse_claim(
        "1. 사용자 질의에 대응하는 문서를 검색하고 검색된 문서의 우선순위를 산출하는 검색모듈",
        llm_parser=lambda _: [
            ParsedClaimElement(
                text="사용자 질의에 대응하는 문서를 검색하는 검색모듈",
                source_span="사용자 질의에 대응하는 문서를 검색하고 검색된 문서의 우선순위를 산출하는 검색모듈",
                parser_confidence=0.9,
                parser_method="llm_assisted",
                parser_status="parsed",
            )
        ],
    )

    assert claim is not None
    assert len(claim.elements) == 1
    assert claim.elements[0].parser_confidence == 0.85
    assert claim.elements[0].parser_method == "llm_assisted"
    assert claim.elements[0].parser_status == "parsed"
    assert claim.parser_confidence == 0.85
    assert claim.parser_method == "llm_assisted"
    assert claim.parser_status == "parsed"


def test_llm_parser_rejects_elements_without_source_span() -> None:
    claim = parse_claim(
        "1. 사용자 질의에 대응하는 문서를 검색하는 검색모듈",
        llm_parser=lambda _: ["원문에 없는 임베딩 기반 추천모듈"],
    )

    assert claim is not None
    assert claim.elements == [
        ParsedClaimElement(
            text="사용자 질의에 대응하는 문서를 검색하는 검색모듈",
            source_span="사용자 질의에 대응하는 문서를 검색하는 검색모듈",
            parser_confidence=0.55,
            parser_method="fallback",
            parser_status="uncertain",
        )
    ]
    assert claim.parser_method == "fallback"
    assert claim.parser_status == "uncertain"


def test_rule_parser_refines_long_processor_clause_for_llm_matching() -> None:
    claim = parse_claim(
        "1. 인공지능을 이용한 기관 내 문서검색 개인화 및 신규문서 작성 장치에서, "
        "데이터를 획득하는 입력 모듈;외부 장치와 상기 데이터를 송수신하는 통신 모듈;"
        "동작의 수행을 위해 적어도 하나의 프로세스가 저장되고 사용자 입력과 데이터를 저장하는 메모리;"
        "그래픽 이미지를 디스플레이하는 디스플레이; 및상기 프로세스에 따라 제어 방법을 수행하는 "
        "프로세서를 포함하되, 상기 프로세서는, 사용자의 검색 기록, 문서 열람 이력, 부서 정보 및 "
        "전자 문서를 포함하는 제 1 데이터를 입력 모듈을 통하여 획득하고, 상기 제 1 데이터를 "
        "전처리하고, 상기 전처리된 제 1 데이터를 학습하고, 학습 결과를 이용하여 문서검색 개인화 "
        "및 신규문서 작성 모델을 생성하고, 요청 메시지를 상기 입력 모듈을 통하여 획득하고, "
        "상기 문서검색 개인화 및 신규문서 작성 모델을 이용하여 상기 요청 메시지에 대응하는 "
        "문서검색 결과 및 신규문서 중 적어도 하나를 생성하고, 상기 디스플레이가 생성 결과를 "
        "디스플레이하도록 제어하고,상기 프로세서는,BERT 기반 컨텍스트 임베딩 엔진 및 "
        "SLM(Supervised Language Model) 구성 모듈을 포함하고,상기 BERT 기반 컨텍스트 임베딩 "
        "엔진은,기록물의 문맥과 의미를 고려한 벡터 표현을 생성하고,상기 SLM 구성 모듈은,"
        "상기 BERT의 출력을 입력으로 받아 상기 모델을 구축하여 지도학습을 수행하고,상기 "
        "프로세서는,상기 신규문서를 작성할 때, 실시간 뉴스를 검색하고, 상기 신규문서 중 상기 "
        "실시간 뉴스와 유사도가 임계값 이상인 문서를 선택하고, 상기 디스플레이가 상기 선택된 "
        "문서를 디스플레이하도록 제어하는, 문서검색 개인화 및 신규문서 작성 장치."
    )

    assert claim is not None
    assert len(claim.elements) > 5
    assert max(len(element.text) for element in claim.elements) < 300
    assert "및상기" not in [element.text[:3] for element in claim.elements]
    assert any("제 1 데이터를 전처리" in element.text for element in claim.elements)
    assert any("문서검색 개인화 및 신규문서 작성 모델을 생성" in element.text for element in claim.elements)
    assert all(element.source_span in claim.normalized_text for element in claim.elements)


def test_normalize_application_number() -> None:
    assert normalize_application_number("10-2006-0033658") == "1020060033658"
