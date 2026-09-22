from abc import ABC, abstractmethod
import hashlib
import math
import os
from typing import Optional


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Embed a single text string into a vector."""
        raise NotImplementedError

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings into vectors."""
        return [self.embed(t) for t in texts]


class HashEmbeddingProvider(EmbeddingProvider):
    """
    A lightweight, deterministic embedding provider for local development and testing.
    Uses SHA-256 feature hashing with L2-normalization to build reproducible vectors.
    """

    def __init__(self, vector_dim: int = 128):
        self.vector_dim = vector_dim

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            return [0.0] * self.vector_dim

        vector = [0.0] * self.vector_dim
        words = text.lower().split()

        for word in words:
            hash_digest = hashlib.sha256(word.encode("utf-8")).digest()
            index = int.from_bytes(hash_digest[:4], "big") % self.vector_dim
            val = (int.from_bytes(hash_digest[4:8], "big") % 2000 - 1000) / 1000.0
            vector[index] += val

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding provider talking to Ollama's native /api/embed endpoint
    (default http://localhost:11434, model nomic-embed-text). embed_batch
    sends all texts in one request, so ingesting a whole paper costs one
    HTTP round-trip instead of one per chunk. Failures surface as
    RuntimeError (or fall back to HashEmbeddingProvider when
    RETRIEVAL_ALLOW_LOCAL_FALLBACK is enabled, mirroring the Azure provider).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        allow_fallback: Optional[bool] = None,
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        self.timeout = timeout

        if allow_fallback is None:
            allow_fallback = (
                os.getenv("RETRIEVAL_ALLOW_LOCAL_FALLBACK", "true").lower()
                == "true"
            )
        self.allow_fallback = allow_fallback
        self._fallback_provider = HashEmbeddingProvider()

    def _embed_remote(self, inputs: list[str], batch_size: int = 16) -> list[list[float]]:
        import httpx

        url = f"{self.base_url}/api/embed"
        all_embeddings: list[list[float]] = []
        with httpx.Client(timeout=self.timeout) as client:
            for i in range(0, len(inputs), batch_size):
                batch = inputs[i : i + batch_size]
                res = client.post(
                    url,
                    json={"model": self.model, "input": batch},
                )
                res.raise_for_status()
                data = res.json()
                embeddings = data.get("embeddings")
                if not embeddings or len(embeddings) != len(batch):
                    raise RuntimeError(
                        f"Ollama embedding response mismatch: expected {len(batch)} "
                        f"vectors, got {len(embeddings or [])}"
                    )
                all_embeddings.extend(embeddings)
        return all_embeddings

    def embed(self, text: str) -> list[float]:
        try:
            return self._embed_remote([text])[0]
        except Exception as err:
            if not self.allow_fallback:
                raise RuntimeError(
                    f"Ollama embedding call failed: {err}"
                ) from err
            return self._fallback_provider.embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            return self._embed_remote(texts)
        except Exception as err:
            if not self.allow_fallback:
                raise RuntimeError(
                    f"Ollama embedding call failed: {err}"
                ) from err
            return self._fallback_provider.embed_batch(texts)


class AzureOpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Production embedding provider targeting Azure OpenAI Service.
    Falls back to HashEmbeddingProvider if RETRIEVAL_ALLOW_LOCAL_FALLBACK is enabled.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        allow_fallback: Optional[bool] = None,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment = deployment

        if allow_fallback is None:
            allow_fallback = (
                os.getenv("RETRIEVAL_ALLOW_LOCAL_FALLBACK", "true").lower()
                == "true"
            )
        self.allow_fallback = allow_fallback
        self._fallback_provider = HashEmbeddingProvider()

    def embed(self, text: str) -> list[float]:
        if not self.endpoint or not self.api_key or not self.deployment:
            if not self.allow_fallback:
                raise RuntimeError(
                    "Azure OpenAI embedding credentials missing and local fallback disabled."
                )
            return self._fallback_provider.embed(text)

        import httpx

        try:
            url = (
                f"{self.endpoint.rstrip('/')}/openai/deployments/"
                f"{self.deployment}/embeddings?api-version=2023-05-15"
            )
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json",
            }
            payload = {"input": text}
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                return data["data"][0]["embedding"]
        except Exception as err:
            if not self.allow_fallback:
                raise RuntimeError(
                    f"Azure OpenAI embedding call failed: {err}"
                ) from err
            return self._fallback_provider.embed(text)
