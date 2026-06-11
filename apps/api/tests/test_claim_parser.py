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
    assert claim.parser_confidence == 0.95


def test_parse_deleted_claim() -> None:
    claim = parse_claim("2. 삭제")

    assert claim is not None
    assert claim.claim_number == 2
    assert claim.status == "deleted"
    assert claim.is_independent is None
    assert claim.elements == []
    assert claim.parser_confidence == 0.95


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
            )
        ],
    )

    assert claim is not None
    assert len(claim.elements) == 1
    assert claim.elements[0].parser_confidence == 0.85
    assert claim.parser_confidence == 0.85


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
            parser_confidence=0.7,
        )
    ]


def test_normalize_application_number() -> None:
    assert normalize_application_number("10-2006-0033658") == "1020060033658"
