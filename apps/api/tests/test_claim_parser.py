from app.services.claim_parser import normalize_application_number, parse_claim


def test_parse_independent_claim() -> None:
    claim = parse_claim(
        "1. 문서가 저장되는 데이터베이스;사용자가 질의어를 입력하기 위한 입력수단;"
        "입력된 질의어로부터 키워드를 추출하기 위한 추출수단;"
    )

    assert claim is not None
    assert claim.claim_number == 1
    assert claim.status == "active"
    assert claim.is_independent is True
    assert claim.dependency_claim_numbers == []
    assert len(claim.elements) == 3


def test_parse_deleted_claim() -> None:
    claim = parse_claim("2. 삭제")

    assert claim is not None
    assert claim.claim_number == 2
    assert claim.status == "deleted"
    assert claim.is_independent is None
    assert claim.elements == []


def test_parse_dependent_claim_with_html_tags() -> None:
    claim = parse_claim(
        '3. <P INDENT="14" ALIGN="JUSTIFIED">제 1 항에 있어서, '
        "상기 추출수단은 파일의 컨텐츠로부터 텍스트를 분류하는 것을 특징으로 하는 시스템.</P>"
    )

    assert claim is not None
    assert claim.claim_number == 3
    assert claim.status == "active"
    assert claim.is_independent is False
    assert claim.dependency_claim_numbers == [1]
    assert "<P" not in claim.normalized_text


def test_normalize_application_number() -> None:
    assert normalize_application_number("10-2006-0033658") == "1020060033658"

