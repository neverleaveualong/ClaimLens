from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.clients.kipris import CLAIM_INFO_URL, ClaimInfoResult, PatentSearchResult, KiprisClient
from app.models.patent import Claim, ClaimElement, Patent
from app.services.claim_parser import ParsedClaim, normalize_application_number, parse_claims


GENERATED_TITLE_PREFIX = "KIPRIS patent "


@dataclass(frozen=True)
class PatentCollectionResult:
    application_number: str
    title: str
    saved_claim_count: int
    active_claim_count: int
    deleted_claim_count: int
    fetch_status: str = "fetched"
    error_message: str | None = None


@dataclass(frozen=True)
class CollectionSummary:
    requested_count: int
    saved_patent_count: int
    failed_patent_count: int
    results: list[PatentCollectionResult] = field(default_factory=list)


@dataclass(frozen=True)
class ClaimCollectionStats:
    saved_count: int
    active_count: int
    deleted_count: int


class KiprisCollector:
    def __init__(self, db: Session, client: KiprisClient) -> None:
        self.db = db
        self.client = client

    def collect_by_keyword(self, keyword: str, limit: int = 10) -> CollectionSummary:
        candidates = self.client.search_patents(keyword=keyword, limit=limit)
        results: list[PatentCollectionResult] = []
        for candidate in candidates:
            results.append(self._collect_candidate_with_transaction(candidate))

        return CollectionSummary(
            requested_count=len(candidates),
            saved_patent_count=sum(1 for result in results if result.fetch_status != "fetch_failed"),
            failed_patent_count=sum(1 for result in results if result.fetch_status == "fetch_failed"),
            results=results,
        )

    def collect_by_application_number(self, application_number: str) -> PatentCollectionResult:
        generated_title = f"{GENERATED_TITLE_PREFIX}{application_number}"
        candidate = PatentSearchResult(
            application_number=application_number,
            title=generated_title,
        )
        return self._collect_candidate_with_transaction(candidate)

    def _collect_candidate_with_transaction(self, candidate: PatentSearchResult) -> PatentCollectionResult:
        try:
            result = self.collect_patent(candidate)
        except Exception as exc:
            self.db.rollback()
            result = self._record_failed_collection(candidate, exc)
        self.db.commit()
        return result

    def collect_patent(self, candidate: PatentSearchResult) -> PatentCollectionResult:
        fetched_at = datetime.now(timezone.utc)
        patent = self._upsert_patent(candidate, fetched_at)
        claim_result = self._fetch_claims(candidate.application_number)
        parsed_claims = self._parse_claims(claim_result.claims)
        stats = self._save_claims(patent, parsed_claims, claim_result, fetched_at)
        self._mark_patent_fetch_complete(patent, stats, fetched_at)

        return PatentCollectionResult(
            application_number=candidate.application_number,
            title=candidate.title,
            saved_claim_count=stats.saved_count,
            active_claim_count=stats.active_count,
            deleted_claim_count=stats.deleted_count,
        )

    def _fetch_claims(self, application_number: str) -> ClaimInfoResult:
        return self.client.get_claims(application_number)

    def _parse_claims(self, raw_claims: list[str]) -> list[ParsedClaim]:
        return parse_claims(raw_claims)

    def _save_claims(
        self,
        patent: Patent,
        parsed_claims: list[ParsedClaim],
        claim_result: ClaimInfoResult,
        fetched_at: datetime,
    ) -> ClaimCollectionStats:
        active_count = 0
        deleted_count = 0

        for parsed_claim in parsed_claims:
            if parsed_claim.status == "deleted":
                deleted_count += 1
            else:
                active_count += 1
            self._upsert_claim(patent, parsed_claim, claim_result, fetched_at)

        return ClaimCollectionStats(
            saved_count=len(parsed_claims),
            active_count=active_count,
            deleted_count=deleted_count,
        )

    def _mark_patent_fetch_complete(
        self,
        patent: Patent,
        stats: ClaimCollectionStats,
        fetched_at: datetime,
    ) -> None:
        patent.fetch_status = "fetched" if stats.saved_count else "no_claims"
        patent.last_fetched_at = fetched_at
        self.db.flush()

    def _record_failed_collection(
        self,
        candidate: PatentSearchResult,
        error: Exception,
    ) -> PatentCollectionResult:
        fetched_at = datetime.now(timezone.utc)
        patent = self._upsert_patent(candidate, fetched_at)
        patent.fetch_status = "fetch_failed"
        patent.last_fetched_at = fetched_at
        self.db.flush()

        return PatentCollectionResult(
            application_number=candidate.application_number,
            title=patent.title,
            saved_claim_count=0,
            active_claim_count=0,
            deleted_claim_count=0,
            fetch_status="fetch_failed",
            error_message=str(error),
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
        if not candidate.title.startswith(GENERATED_TITLE_PREFIX) or not patent.title:
            patent.title = candidate.title or candidate.application_number

        self._assign_if_present(patent, "abstract", candidate.abstract)
        self._assign_if_present(patent, "applicant_name", candidate.applicant_name)
        self._assign_if_present(patent, "ipc_number", candidate.ipc_number)
        self._assign_if_present(patent, "application_date", candidate.application_date)
        self._assign_if_present(patent, "register_status", candidate.register_status)
        self._assign_if_present(patent, "register_number", candidate.register_number)
        self._assign_if_present(patent, "publication_number", candidate.publication_number)
        self._assign_if_present(patent, "open_number", candidate.open_number)
        patent.source = "kipris"
        patent.source_url = CLAIM_INFO_URL
        patent.fetch_status = "fetching"
        patent.last_fetched_at = fetched_at
        self.db.flush()
        return patent

    @staticmethod
    def _assign_if_present(model: Patent, field_name: str, value: str | None) -> None:
        if value is not None:
            setattr(model, field_name, value)

    def _upsert_claim(
        self,
        patent: Patent,
        parsed_claim: ParsedClaim,
        claim_result: ClaimInfoResult,
        fetched_at: datetime,
    ) -> Claim:
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
                source_endpoint=claim_result.source_endpoint,
                source_document_type=claim_result.source_document_type,
            )
            self.db.add(claim)

        claim.raw_text = parsed_claim.raw_text
        claim.normalized_text = parsed_claim.normalized_text
        claim.status = parsed_claim.status
        claim.is_independent = parsed_claim.is_independent
        claim.dependency_claim_numbers = self._serialize_dependency_claim_numbers(parsed_claim)
        claim.source_endpoint = claim_result.source_endpoint
        claim.source_document_type = claim_result.source_document_type
        claim.parser_confidence = parsed_claim.parser_confidence
        claim.parser_method = parsed_claim.parser_method
        claim.parser_status = parsed_claim.parser_status
        claim.last_fetched_at = fetched_at
        self.db.flush()

        self._replace_claim_elements(claim, parsed_claim)
        return claim

    def _serialize_dependency_claim_numbers(self, parsed_claim: ParsedClaim) -> str:
        return ",".join(str(number) for number in parsed_claim.dependency_claim_numbers)

    def _replace_claim_elements(self, claim: Claim, parsed_claim: ParsedClaim) -> None:
        self.db.query(ClaimElement).filter(ClaimElement.claim_id == claim.id).delete()
        self.db.flush()
        for index, element in enumerate(parsed_claim.elements, start=1):
            claim.elements.append(
                ClaimElement(
                    element_order=index,
                    element_text=element.text,
                    source_span=element.source_span,
                    parser_confidence=element.parser_confidence,
                    parser_method=element.parser_method,
                    parser_status=element.parser_status,
                )
            )
