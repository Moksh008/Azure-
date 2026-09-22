"""Shared helper for normalizing Azure AI Foundry endpoint URLs.

AZURE_OPENAI_ENDPOINT may be set to either the bare resource host
(`https://<resource>.services.ai.azure.com`) or the project endpoint shown
in the Foundry portal (`https://<resource>.services.ai.azure.com/api/
projects/<project>`). The unified model-inference API used for both chat
and embeddings lives at `/models/...` directly on the resource host, not
under `/api/projects/<project>`, so any path must be stripped.
"""

from __future__ import annotations

from urllib.parse import urlsplit


def resource_host(endpoint: str) -> str:
    parts = urlsplit(endpoint)
    if not parts.scheme or not parts.netloc:
        return endpoint.rstrip("/")
    return f"{parts.scheme}://{parts.netloc}"
