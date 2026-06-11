from __future__ import annotations

import html
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass


CLAIM_NUMBER_RE = re.compile(r"^\s*(\d+)\s*\.")
TAG_RE = re.compile(r"<[^>]+>")
DEPENDENCY_PATTERNS = (
    re.compile(r"제\s*(\d+)\s*항"),
    re.compile(r"청구항\s*(\d+)"),
    re.compile(r"claim\s+(\d+)", re.IGNORECASE),
)
CLAIM_ELEMENT_SPLIT_RE = re.compile(
    r";|；|(?<=단계),|(?<=수단),|(?<=모듈),|(?<=부),|(?<=포함하는),"
)
MAX_ELEMENTS_PER_CLAIM = 12
RULE_SPLIT_CONFIDENCE = 0.75
RULE_SINGLE_ELEMENT_CONFIDENCE = 0.55
RULE_UNSPLIT_CONFIDENCE = 0.5
LLM_VALIDATED_CONFIDENCE = 0.85
CONFIDENT_RULE_SPLIT_THRESHOLD = 0.8


@dataclass(frozen=True)
class ParsedClaimElement:
    text: str
    source_span: str
    parser_confidence: float


@dataclass(frozen=True)
class ParsedClaim:
    claim_number: int
    raw_text: str
    normalized_text: str
    status: str
    is_independent: bool | None
    dependency_claim_numbers: list[int]
    elements: list[ParsedClaimElement]
    parser_confidence: float


LLMElementParser = Callable[[str], Iterable[str | ParsedClaimElement]]


def normalize_application_number(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_claim_text(raw_text: str) -> str:
    without_tags = TAG_RE.sub(" ", raw_text)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def extract_claim_number(normalized_text: str) -> int | None:
    match = CLAIM_NUMBER_RE.match(normalized_text)
    if not match:
        return None
    return int(match.group(1))


def extract_dependency_claim_numbers(claim_body: str) -> list[int]:
    numbers: set[int] = set()
    for pattern in DEPENDENCY_PATTERNS:
        for match in pattern.finditer(claim_body):
            numbers.add(int(match.group(1)))
    return sorted(numbers)


def split_claim_elements(claim_body: str) -> list[ParsedClaimElement]:
    compact = re.sub(r"\s+", " ", claim_body).strip()
    if not compact:
        return []

    raw_parts = CLAIM_ELEMENT_SPLIT_RE.split(compact)
    parts = [part.strip(" ,") for part in raw_parts if len(part.strip(" ,")) >= 4]
    if not parts:
        return [
            ParsedClaimElement(
                text=compact,
                source_span=compact,
                parser_confidence=RULE_UNSPLIT_CONFIDENCE,
            )
        ]

    confidence = RULE_SPLIT_CONFIDENCE if len(parts) > 1 else RULE_SINGLE_ELEMENT_CONFIDENCE
    return [
        ParsedClaimElement(text=part, source_span=part, parser_confidence=confidence)
        for part in parts[:MAX_ELEMENTS_PER_CLAIM]
    ]


def parse_claims(raw_claims: Iterable[str]) -> list[ParsedClaim]:
    parsed_claims: list[ParsedClaim] = []
    for raw_claim in raw_claims:
        parsed_claim = parse_claim(raw_claim)
        if parsed_claim is not None:
            parsed_claims.append(parsed_claim)
    return parsed_claims


def select_independent_claims(
    parsed_claims: Iterable[ParsedClaim],
    max_claims: int = 3,
) -> list[ParsedClaim]:
    candidates = [
        claim
        for claim in parsed_claims
        if claim.status == "active" and claim.is_independent is True
    ]
    return sorted(candidates, key=lambda claim: claim.claim_number)[:max_claims]


def parse_claim(
    raw_claim: str,
    *,
    llm_parser: LLMElementParser | None = None,
) -> ParsedClaim | None:
    raw_text = raw_claim.strip()
    normalized_text = normalize_claim_text(raw_text)
    claim_number = extract_claim_number(normalized_text)
    if claim_number is None:
        return None

    claim_body = CLAIM_NUMBER_RE.sub("", normalized_text, count=1).strip()
    status = "deleted" if claim_body == "삭제" else "active"
    dependencies = extract_dependency_claim_numbers(claim_body)
    is_independent = None if status == "deleted" else len(dependencies) == 0
    elements = _parse_elements(claim_body, status, llm_parser)
    parser_confidence = _claim_confidence(status, elements)

    return ParsedClaim(
        claim_number=claim_number,
        raw_text=raw_text,
        normalized_text=normalized_text,
        status=status,
        is_independent=is_independent,
        dependency_claim_numbers=dependencies,
        elements=elements,
        parser_confidence=parser_confidence,
    )


def _parse_elements(
    claim_body: str,
    status: str,
    llm_parser: LLMElementParser | None,
) -> list[ParsedClaimElement]:
    if status != "active":
        return []

    rule_elements = split_claim_elements(claim_body)
    if _has_confident_rule_split(rule_elements):
        return rule_elements

    if llm_parser is None:
        return rule_elements

    llm_elements = _validated_llm_elements(claim_body, llm_parser(claim_body))
    return llm_elements or rule_elements


def _has_confident_rule_split(elements: list[ParsedClaimElement]) -> bool:
    return (
        len(elements) > 1
        and min(element.parser_confidence for element in elements)
        >= CONFIDENT_RULE_SPLIT_THRESHOLD
    )


def _validated_llm_elements(
    claim_body: str,
    candidate_elements: Iterable[str | ParsedClaimElement],
) -> list[ParsedClaimElement]:
    elements: list[ParsedClaimElement] = []
    for candidate in candidate_elements:
        if isinstance(candidate, ParsedClaimElement):
            text = candidate.text.strip()
            source_span = candidate.source_span.strip()
        else:
            text = str(candidate).strip()
            source_span = text

        if len(text) < 4 or not source_span or source_span not in claim_body:
            continue

        elements.append(
            ParsedClaimElement(
                text=text,
                source_span=source_span,
                parser_confidence=LLM_VALIDATED_CONFIDENCE,
            )
        )
        if len(elements) >= MAX_ELEMENTS_PER_CLAIM:
            break

    return elements


def _claim_confidence(status: str, elements: list[ParsedClaimElement]) -> float:
    if status == "deleted":
        return 0.95
    if not elements:
        return 0.0
    return min(element.parser_confidence for element in elements)
