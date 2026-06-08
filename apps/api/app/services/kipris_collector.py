from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.clients.kipris import CLAIM_INFO_URL, PatentSearchResult, KiprisClient
from app.models.patent import Claim, ClaimElement, Patent
from app.services.claim_parser import normalize_application_number, parse_claim


@dataclass(frozen=True)
class PatentCollectionResult:
    application_number: str
    title: str
    saved_claim_count: int
    active_claim_count: int
    deleted_claim_count: int


@dataclass(frozen=True)
class CollectionSummary:
    requested_count: int
    saved_patent_count: int
    results: list[PatentCollectionResult] = field(default_factory=list)


class KiprisCollector:
    def __init__(self, db: Session, client: KiprisClient) -> None:
        self.db = db
        self.client = client

    def collect_by_keyword(self, keyword: str, limit: int = 10) -> CollectionSummary:
        candidates = self.client.search_patents(keyword=keyword, limit=limit)
        results = [self.collect_patent(candidate) for candidate in candidates]
        self.db.commit()
        return CollectionSummary(
            requested_count=len(candidates),
            saved_patent_count=len(results),
            results=results,
        )

    def collect_by_application_number(self, application_number: str) -> PatentCollectionResult:
        generated_title = f"KIPRIS patent {application_number}"
        candidate = PatentSearchResult(
            application_number=application_number,
            title=generated_title,
        )
        result = self.collect_patent(candidate)
        self.db.commit()
        return result

    def collect_patent(self, candidate: PatentSearchResult) -> PatentCollectionResult:
        fetched_at = datetime.now(timezone.utc)
        patent = self._upsert_patent(candidate, fetched_at)
        claim_result = self.client.get_claims(candidate.application_number)

        saved_count = 0
        active_count = 0
        deleted_count = 0
        for raw_claim in claim_result.claims:
            parsed_claim = parse_claim(raw_claim)
            if parsed_claim is None:
                continue

            saved_count += 1
            if parsed_claim.status == "deleted":
                deleted_count += 1
            else:
                active_count += 1
            self._upsert_claim(patent, parsed_claim, fetched_at)

        patent.fetch_status = "fetched" if saved_count else "no_claims"
        patent.last_fetched_at = fetched_at
        self.db.flush()

        return PatentCollectionResult(
            application_number=candidate.application_number,
            title=candidate.title,
            saved_claim_count=saved_count,
            active_claim_count=active_count,
            deleted_claim_count=deleted_count,
        )

    def _upsert_patent(self, candidate: PatentSearchResult, fetched_at: datetime) -> Patent:
        normalized = normalize_application_number(candidate.application_number)
        patent = (
            self.db.query(Patent)
            .filter(Patent.application_number_normalized == normalized)
            .one_or_none()
        )
        if patent is None:
            patent = Patent(
                application_number=candidate.application_number,
                application_number_normalized=normalized,
                title=candidate.title or candidate.application_number,
            )
            self.db.add(patent)

        patent.application_number = candidate.application_number
        patent.application_number_normalized = normalized
        if not candidate.title.startswith("KIPRIS patent ") or not patent.title:
            patent.title = candidate.title or candidate.application_number
        patent.abstract = candidate.abstract
        patent.applicant_name = candidate.applicant_name
        patent.ipc_number = candidate.ipc_number
        patent.application_date = candidate.application_date
        patent.register_status = candidate.register_status
        patent.register_number = candidate.register_number
        patent.publication_number = candidate.publication_number
        patent.open_number = candidate.open_number
        patent.source = "kipris"
        patent.source_url = CLAIM_INFO_URL
        patent.fetch_status = "fetching"
        patent.last_fetched_at = fetched_at
        self.db.flush()
        return patent

    def _upsert_claim(self, patent: Patent, parsed_claim, fetched_at: datetime) -> Claim:
        claim = (
            self.db.query(Claim)
            .filter(
                Claim.patent_id == patent.id,
                Claim.claim_number == parsed_claim.claim_number,
            )
            .one_or_none()
        )
        if claim is None:
            claim = Claim(
                patent_id=patent.id,
                claim_number=parsed_claim.claim_number,
                raw_text=parsed_claim.raw_text,
                normalized_text=parsed_claim.normalized_text,
                source_endpoint="patentClaimInfo",
                source_document_type="claim_endpoint",
            )
            self.db.add(claim)

        claim.raw_text = parsed_claim.raw_text
        claim.normalized_text = parsed_claim.normalized_text
        claim.status = parsed_claim.status
        claim.is_independent = parsed_claim.is_independent
        claim.dependency_claim_numbers = ",".join(str(number) for number in parsed_claim.dependency_claim_numbers)
        claim.source_endpoint = "patentClaimInfo"
        claim.source_document_type = "claim_endpoint"
        claim.parser_confidence = parsed_claim.parser_confidence
        claim.last_fetched_at = fetched_at
        self.db.flush()

        self.db.query(ClaimElement).filter(ClaimElement.claim_id == claim.id).delete()
        self.db.flush()
        for index, element_text in enumerate(parsed_claim.elements, start=1):
            claim.elements.append(
                ClaimElement(
                    element_order=index,
                    element_text=element_text,
                    source_span=element_text,
                    parser_confidence=parsed_claim.parser_confidence,
                )
            )
        return claim
