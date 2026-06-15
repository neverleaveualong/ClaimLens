from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.services.vector_search import PineconeClaimVectorIndex, build_claim_vector_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Index ClaimLens patents and claims into Pinecone")
    parser.add_argument("--namespace", default=None, help="Pinecone namespace")
    parser.add_argument("--limit", type=int, default=None, help="Limit patents read from PostgreSQL")
    parser.add_argument("--clear-namespace", action="store_true", help="Delete namespace vectors first")
    parser.add_argument("--skip-abstracts", action="store_true", help="Do not index patent abstracts")
    parser.add_argument("--skip-claims", action="store_true", help="Do not index full independent claims")
    parser.add_argument("--skip-elements", action="store_true", help="Do not index claim elements")
    args = parser.parse_args()

    vector_index = PineconeClaimVectorIndex(namespace=args.namespace)
    vector_index.ensure_index()
    if args.clear_namespace:
        vector_index.clear_namespace()

    with SessionLocal() as db:
        documents = build_claim_vector_documents(
            db,
            include_patent_abstracts=not args.skip_abstracts,
            include_independent_claims=not args.skip_claims,
            include_claim_elements=not args.skip_elements,
            limit=args.limit,
        )

    saved = vector_index.upsert_documents(documents)
    print(f"indexed={saved} namespace={vector_index.namespace} index={vector_index.index_name}")


if __name__ == "__main__":
    main()
