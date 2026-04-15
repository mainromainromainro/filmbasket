from __future__ import annotations

import re
import string
from typing import Any

from rapidfuzz import fuzz, process


def _normalize_text(value: str) -> str:
    lowered = value.lower().strip()
    no_punct = lowered.translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", no_punct).strip()


def match_product(title_raw: str, catalog: list[dict[str, Any]]) -> tuple[str | None, float]:
    normalized_title = _normalize_text(title_raw)

    if not normalized_title:
        return None, 0.0

    for row in catalog:
        canonical = str(row.get("canonical_name", "")).strip()
        canonical_norm = _normalize_text(canonical)
        if canonical_norm and canonical_norm in normalized_title:
            return canonical, 1.0

    for row in catalog:
        canonical = str(row.get("canonical_name", "")).strip()
        aliases = str(row.get("aliases", "")).split(",")
        for alias in aliases:
            alias_norm = _normalize_text(alias)
            if alias_norm and alias_norm in normalized_title:
                return canonical, 0.9

    choices: list[str] = []
    choice_map: dict[str, str] = {}
    for row in catalog:
        canonical = str(row.get("canonical_name", "")).strip()
        canonical_norm = _normalize_text(canonical)
        if canonical_norm:
            choices.append(canonical_norm)
            choice_map[canonical_norm] = canonical

    if not choices:
        return None, 0.0

    result = process.extractOne(normalized_title, choices, scorer=fuzz.token_sort_ratio)
    if result is None:
        return None, 0.0

    best_match, score, _ = result
    if score >= 70:
        return choice_map.get(best_match), float(score) / 100.0
    return None, 0.0
