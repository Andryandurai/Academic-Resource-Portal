"""Turn one free-text WhatsApp message into (subject phrase, unit, kind).

Two extractors, run in that order:

1. **Alias matching** (`_extract_aliases`) — always runs, costs nothing, and is
   exact: "unit 1", "cat2", "youtube videos" are matched against the same
   vocabulary the website menus use (`catalog.match_unit_alias` /
   `match_kind_alias`), then stripped out of the sentence. It alone is enough
   for the direct form the spec gives as an example: "unit 1 data structure
   notes" needs no LLM at all.
2. **LLM cleanup** (`_llm_subject`) — only for the subject phrase, and only
   when a noisy sentence ("umm can you get me the ds unit 1 notes pls") leaves
   a remainder too mangled for the fuzzy matcher in `catalog.py`. The LLM is
   never asked for unit or kind: those are a closed, exact vocabulary, and a
   keyword match beats an LLM guess on both cost and reliability. If the call
   fails, times out, or `GROQ_API_KEY` is unset, this step is skipped
   silently and the alias-stripped remainder is used as-is — the bot degrades
   to rule-based-only rather than going down.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import requests
from django.conf import settings

from . import catalog

logger = logging.getLogger(__name__)

_LLM_TIMEOUT_SECONDS = 6

# Longest aliases first so "semester exam" is not shadowed by a hypothetical
# shorter alias contained inside it.
_UNIT_PATTERN = re.compile(
    "|".join(sorted((re.escape(k) for k in catalog.UNIT_ALIASES), key=len, reverse=True)),
    re.IGNORECASE,
)
_KIND_PATTERN = re.compile(
    "|".join(sorted((re.escape(k) for k in catalog.KIND_ALIASES), key=len, reverse=True)),
    re.IGNORECASE,
)


@dataclass
class Intent:
    subject_query: str
    unit: str | None
    kind: str | None


def extract_intent(text: str) -> Intent:
    unit, kind, remainder = _extract_aliases(text)
    subject_query = _llm_subject(text) or remainder
    return Intent(subject_query=subject_query.strip(), unit=unit, kind=kind)


def _extract_aliases(text: str) -> tuple[str | None, str | None, str]:
    unit = None
    m = _UNIT_PATTERN.search(text)
    if m:
        unit = catalog.match_unit_alias(m.group(0))
        text = text[: m.start()] + " " + text[m.end() :]

    kind = None
    m = _KIND_PATTERN.search(text)
    if m:
        kind = catalog.match_kind_alias(m.group(0))
        text = text[: m.start()] + " " + text[m.end() :]

    return unit, kind, " ".join(text.split())


def _llm_subject(original_text: str) -> str | None:
    """Ask the free-tier LLM for just the course-name phrase, or None.

    Deliberately narrow: one field, strict JSON, temperature 0. A model asked
    to do less has less room to hallucinate a unit or kind that disagrees with
    the deterministic alias match above.
    """
    if not settings.GROQ_API_KEY:
        return None

    prompt = (
        "Extract only the academic subject or course name the student is asking "
        "about, exactly as they phrased it, with filler words removed. "
        "Ignore any unit number, CAT, exam or file-type wording — that is handled "
        "elsewhere. Reply with strict JSON only: {\"subject\": \"...\"} or "
        '{"subject": null} if no subject is mentioned.\n\n'
        f"Message: {original_text!r}"
    )
    try:
        response = requests.post(
            f"{settings.GROQ_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": settings.GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 100,
                "response_format": {"type": "json_object"},
            },
            timeout=_LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        subject = json.loads(content).get("subject")
        return subject.strip() if isinstance(subject, str) and subject.strip() else None
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError) as exc:
        # Network hiccup, free-tier rate limit, or a malformed reply from the
        # model — all fall back to the alias-stripped remainder, never a crash.
        logger.warning("LLM subject extraction skipped: %s", exc)
        return None
