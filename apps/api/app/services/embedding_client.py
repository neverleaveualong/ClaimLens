from __future__ import annotations

from collections.abc import Sequence

from openai import OpenAI

from app.core.config import settings


class OpenAIEmbeddingClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        resolved_api_key = api_key or settings.openai_api_key
        if not resolved_api_key:
            raise ValueError("OPENAI_API_KEY is missing.")

        self.model = model or settings.openai_embedding_model
        self.client = OpenAI(api_key=resolved_api_key)

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self.client.embeddings.create(
            model=self.model,
            input=list(texts),
        )
        return [item.embedding for item in response.data]
