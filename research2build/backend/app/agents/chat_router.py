"""Intent classifier for the unified chat workflow.

The chat endpoint (`POST /chat` in main.py) is a thin orchestrator: this
module's only job is to decide *what the user wants* and hand back
structured args, so main.py can call the same pipeline functions the
dedicated /discovery, /analysis, and /qa routes already call. No business
logic lives here — just routing.

Same prompt-for-JSON pattern as qa.py/analyzer.py: ask the model for a
JSON object, parse it, fail loudly on garbage rather than guessing.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from backend.app.services.llm_service import AzureFoundryLLMService, LLMService

LLMServiceType = LLMService | AzureFoundryLLMService

VALID_INTENTS = {"search", "analyze", "ask", "chat"}


class LibrarySummaryEntry(BaseModel):
    paper_id: str
    title: str
    source: str


class ChatIntent(BaseModel):
    intent: str  # "search" | "analyze" | "ask" | "chat"
    query: str | None = None  # for "search"
    paper_id: str | None = None  # for "analyze" — resolved against the library
    question: str | None = None  # for "ask"
    reply: str | None = None  # for "chat" — the conversational reply itself


def _format_library(library: list[LibrarySummaryEntry]) -> str:
    if not library:
        return "(empty — no papers uploaded or found yet)"
    return "\n".join(f"- id={p.paper_id!r} title={p.title!r} source={p.source}" for p in library)


def _format_history(history: list[dict]) -> str:
    if not history:
        return "(no prior messages)"
    lines = []
    for turn in history[-6:]:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def classify_intent(
    llm_service: LLMServiceType,
    message: str,
    history: list[dict],
    library: list[LibrarySummaryEntry],
    has_selected_evidence: bool,
) -> ChatIntent:
    prompt = f"""
You are the router for a research-paper assistant. Decide what the user's
latest message is asking for, and return ONLY valid JSON — nothing else.

Conversation so far:
{_format_history(history)}

Papers currently in the user's library (id / title / source):
{_format_library(library)}

The user currently has {"some" if has_selected_evidence else "no"} papers
selected (ticked) to answer questions from.

User's latest message:
{message}

Decide exactly one intent:

1. "search" — the user wants to find papers on a topic (e.g. "find papers
   about X", "search for Y"). Extract the topic into "query".
2. "ask" — the DEFAULT for any question about paper content: summaries
   ("what is this paper about?", "summarize it"), specific facts
   ("what dataset did they use?"), or open questions ("what are the
   limitations?", "what's missing here?"). This is fast — a single
   grounded answer with citations. Put the question text in "question".
   Prefer this over "analyze" whenever a plain answer would satisfy the
   user; do not require a full structured breakdown for it.
3. "analyze" — ONLY when the user explicitly asks for a structured
   breakdown/analysis/report of the paper(s) as a whole (e.g. "analyze
   this paper", "give me a full breakdown", "extract problem/method/
   results/limitations for each paper"), not for a single question about
   one aspect — that's "ask" instead, even if the aspect is "limitations"
   or "results".
   - If the message names ONE specific paper (by title or explicit id),
     resolve "paper_id" by matching it against the library list above.
   - If the message refers to multiple/all papers ("these papers", "all
     of them", "each paper", "every paper I selected", or just says
     "analyze" with no paper named while several are selected), leave
     "paper_id" as null — this means "analyze every currently selected
     paper", not "ask for clarification".
   - Only fall back to "chat" asking which paper if the library has
     MULTIPLE papers and the message is ambiguous about whether it means
     one or all of them.
4. "chat" — anything else: greetings, clarification requests, or when you
   cannot confidently resolve "search"/"analyze"/"ask". Put your reply to
   the user directly in "reply" (concise, helpful, plain text).

Return ONLY valid JSON with this exact structure:

{{
  "intent": "search" | "analyze" | "ask" | "chat",
  "query": "string or null",
  "paper_id": "string or null",
  "question": "string or null",
  "reply": "string or null"
}}
"""

    response = llm_service.generate(
        prompt,
        system_prompt=(
            "You are a strict intent router. You output only valid JSON, "
            "never prose, never markdown fences."
        ),
        temperature=0.0,
    )

    data = _parse_response(response)

    intent = data.get("intent")
    if intent not in VALID_INTENTS:
        return ChatIntent(
            intent="chat",
            reply=data.get("reply") or "I didn't quite catch what you'd like to do — could you rephrase?",
        )

    return ChatIntent(
        intent=intent,
        query=data.get("query"),
        paper_id=data.get("paper_id"),
        question=data.get("question"),
        reply=data.get("reply"),
    )


def _parse_response(response: str) -> dict:
    text = response.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"intent": "chat", "reply": None}
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"intent": "chat", "reply": None}

    if not isinstance(data, dict):
        return {"intent": "chat", "reply": None}

    return data
