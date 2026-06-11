from __future__ import annotations

import argparse

from app.clients.kipris import KiprisClient
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.kipris_collector import KiprisCollector


def main() -> None:
    parser = argparse.ArgumentParser(description="KIPRIS patent claim collector")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--keyword", help="KIPRIS search keyword")
    source.add_argument("--application-number", help="KIPRIS application number")
    parser.add_argument("--limit", type=int, default=10, help="Max search result count")
    args = parser.parse_args()

    if not settings.kipris_api_key:
        raise SystemExit("KIPRIS_API_KEY is missing. Add it to apps/api/.env or project .env.")

    client = KiprisClient(settings.kipris_api_key)
    with SessionLocal() as db:
        collector = KiprisCollector(db=db, client=client)
        if args.keyword:
            summary = collector.collect_by_keyword(keyword=args.keyword, limit=args.limit)
            print(
                f"requested={summary.requested_count} "
                f"saved={summary.saved_patent_count} "
                f"failed={summary.failed_patent_count}"
            )
            for result in summary.results:
                print(
                    f"{result.application_number} "
                    f"status={result.fetch_status} "
                    f"claims={result.saved_claim_count} "
                    f"active={result.active_claim_count} "
                    f"deleted={result.deleted_claim_count} "
                    f"title={result.title}"
                )
                if result.error_message:
                    print(f"  error={result.error_message}")
        else:
            result = collector.collect_by_application_number(args.application_number)
            print(
                f"{result.application_number} "
                f"status={result.fetch_status} "
                f"claims={result.saved_claim_count} "
                f"active={result.active_claim_count} "
                f"deleted={result.deleted_claim_count} "
                f"title={result.title}"
            )
            if result.error_message:
                print(f"error={result.error_message}")


if __name__ == "__main__":
    main()
