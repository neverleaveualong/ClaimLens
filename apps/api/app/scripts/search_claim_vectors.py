from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.services.vector_search import PineconeClaimVectorIndex, search_claim_candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Search ClaimLens Pinecone vectors")
    parser.add_argument("query", help="Product or technology description")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    parser.add_argument("--namespace", default=None, help="Pinecone namespace")
    args = parser.parse_args()

    vector_index = PineconeClaimVectorIndex(namespace=args.namespace)
    with SessionLocal() as db:
        candidates = search_claim_candidates(
            db,
            args.query,
            top_k=args.top_k,
            vector_index=vector_index,
        )

    for index, candidate in enumerate(candidates, start=1):
        print(
            f"{index}. score={candidate.score:.4f} "
            f"type={candidate.matched_text_type} "
            f"application={candidate.patent.application_number} "
            f"claim={candidate.claim.claim_number if candidate.claim else '-'} "
            f"element={candidate.matched_claim_element.element_order if candidate.matched_claim_element else '-'}"
        )
        print(f"   title={candidate.patent.title}")
        print(f"   text={candidate.matched_text}")


if __name__ == "__main__":
    main()
