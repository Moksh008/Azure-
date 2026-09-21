"""Search every configured paper source at once and merge the results.

OpenAlex is always queried; CORE is added when CORE_API_KEY is set. Sources
run in parallel, results are interleaved (so neither source's top hits are
buried) and de-duplicated by DOI, falling back to normalized title. One
source failing doesn't fail the search — only all of them failing does.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor

import requests

from backend.app.discovery.core_client import CoreClient
from backend.app.discovery.openalex_client import OpenAlexClient
from backend.app.discovery.paper_models import Paper

logger = logging.getLogger("research2build.discovery")


def _dedupe_key(paper: Paper) -> str:
    if paper.doi:
        return "doi:" + re.sub(r"^https?://(dx\.)?doi\.org/", "", paper.doi.lower())
    return "title:" + re.sub(r"[^a-z0-9]", "", paper.title.lower())


def _merge_into(kept: Paper, duplicate: Paper) -> None:
    """Fill gaps in the first-seen record from its duplicate — e.g. an
    OpenAlex hit with no PDF link picks up CORE's open-access download."""
    kept.pdf_url = kept.pdf_url or duplicate.pdf_url
    kept.abstract = kept.abstract or duplicate.abstract
    kept.url = kept.url or duplicate.url


def _dedupe(papers: list[Paper]) -> list[Paper]:
    merged: dict[str, Paper] = {}
    for paper in papers:
        key = _dedupe_key(paper)
        if key in merged:
            _merge_into(merged[key], paper)
        else:
            merged[key] = paper
    return list(merged.values())


def search_all_sources(query: str, max_results: int = 20) -> list[Paper]:
    sources = [("OpenAlex", OpenAlexClient())]
    core = CoreClient.from_env()
    if core is not None:
        sources.append(("CORE", core))

    def run(source: tuple[str, object]) -> tuple[str, list[Paper] | Exception]:
        name, client = source
        try:
            return name, client.search_papers(query, max_results=max_results)
        except requests.RequestException as exc:
            logger.warning("%s search failed: %s", name, exc)
            return name, exc

    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        outcomes = list(pool.map(run, sources))

    failures = [r for _, r in outcomes if isinstance(r, Exception)]
    if len(failures) == len(outcomes):
        raise failures[0]

    result_lists = [r for _, r in outcomes if not isinstance(r, Exception)]

    merged: dict[str, Paper] = {}
    for rank in range(max((len(r) for r in result_lists), default=0)):
        for results in result_lists:
            if rank >= len(results):
                continue
            paper = results[rank]
            key = _dedupe_key(paper)
            if key in merged:
                _merge_into(merged[key], paper)
            else:
                merged[key] = paper

    return list(merged.values())[:max_results]


def search_core_first(query: str, max_results: int = 20) -> tuple[list[Paper], str]:
    """Search CORE; fall back to OpenAlex if CORE isn't configured, errors
    (e.g. rate-limited), or finds nothing. Returns the papers and the name of
    the source that actually produced them, so callers can tell the user.
    """
    core = CoreClient.from_env()
    if core is not None:
        try:
            papers = _dedupe(core.search_papers(query, max_results=max_results))
            if papers:
                return papers, "CORE"
            logger.info("CORE found nothing for %r; falling back to OpenAlex", query)
        except requests.RequestException as exc:
            logger.warning("CORE search failed, falling back to OpenAlex: %s", exc)

    return OpenAlexClient().search_papers(query, max_results=max_results), "OpenAlex"
