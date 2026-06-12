from __future__ import annotations

import argparse

from app.services.vector_search import PineconeClaimVectorIndex


def main() -> None:
    parser = argparse.ArgumentParser(description="Search ClaimLens Pinecone vectors")
    parser.add_argument("query", help="Product or technology description")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    parser.add_argument("--namespace", default=None, help="Pinecone namespace")
    args = parser.parse_args()

    vector_index = PineconeClaimVectorIndex(namespace=args.namespace)
    results = vector_index.search(args.query, top_k=args.top_k)
    for index, result in enumerate(results, start=1):
        metadata = result.metadata
        print(
            f"{index}. score={result.score:.4f} "
            f"type={metadata.get('text_type')} "
            f"application={metadata.get('application_number')} "
            f"claim={metadata.get('claim_number')} "
            f"element={metadata.get('element_order')}"
        )
        print(f"   title={metadata.get('title')}")
        print(f"   text={result.text}")


if __name__ == "__main__":
    main()
