from __future__ import annotations

import html
import re
from dataclasses import dataclass


CLAIM_NUMBER_RE = re.compile(r"^\s*(\d+)\s*\.")
TAG_RE = re.compile(r"<[^>]+>")
DEPENDENCY_PATTERNS = (
    re.compile(r"제\s*(\d+)\s*항"),
    re.compile(r"청구항\s*(\d+)"),
    re.compile(r"claim\s+(\d+)", re.IGNORECASE),
)


@dataclass(frozen=True)
class ParsedClaim:
    claim_number: int
    raw_text: str
    normalized_text: str
    status: str
    is_independent: bool | None
    dependency_claim_numbers: list[int]
    elements: list[str]
    parser_confidence: float


def normalize_application_number(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def parse_claim(raw_claim: str) -> ParsedClaim | None:
    raw_text = raw_claim.strip()
    normalized_text = normalize_claim_text(raw_text)
    claim_number = extract_claim_number(normalized_text)
    if claim_number is None:
        return None

    claim_body = CLAIM_NUMBER_RE.sub("", normalized_text, count=1).strip()
    status = "deleted" if claim_body == "삭제" else "active"
    dependencies = extract_dependency_claim_numbers(claim_body)
    is_independent = None if status == "deleted" else len(dependencies) == 0
    elements = split_claim_elements(claim_body) if status == "active" else []

    return ParsedClaim(
        claim_number=claim_number,
        raw_text=raw_text,
        normalized_text=normalized_text,
        status=status,
        is_independent=is_independent,
        dependency_claim_numbers=dependencies,
        elements=elements,
        parser_confidence=0.95 if status == "deleted" or elements else 0.75,
    )


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


def split_claim_elements(claim_body: str) -> list[str]:
    compact = re.sub(r"\s+", " ", claim_body).strip()
    if not compact:
        return []

    raw_parts = re.split(r";|；|(?<=단계),|(?<=수단),|(?<=모듈),", compact)
    parts = [part.strip(" ,") for part in raw_parts if len(part.strip(" ,")) >= 4]
    return parts or [compact]

