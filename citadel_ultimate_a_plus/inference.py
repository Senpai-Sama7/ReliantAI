"""ML-based location extraction and vertical classification.

Falls back gracefully when models are not installed.
"""
from __future__ import annotations

import logging
from collections import Counter

logger = logging.getLogger("citadel.inference")

# US state abbreviations for classification
_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

# ---------------------------------------------------------------------------
# Location extraction via spaCy NER
# ---------------------------------------------------------------------------

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_trf")
    return _nlp


def extract_location(texts: list[str]) -> dict:
    """Extract city and state from *texts* using spaCy NER.

    Returns ``{"city": str|None, "state": str|None}``.
    Returns Nones on any failure (model missing, etc.) so callers can fall back.
    """
    try:
        nlp = _get_nlp()
    except OSError:
        logger.debug("spaCy model not installed, returning None")
        return {"city": None, "state": None}

    cities: Counter[str] = Counter()
    states: Counter[str] = Counter()

    for text in texts:
        doc = nlp(text[:10000])
        for ent in doc.ents:
            if ent.label_ == "GPE":
                val = ent.text.strip()
                if val.upper() in _US_STATES and len(val) == 2:
                    states[val.upper()] += 1
                else:
                    cities[val] += 1

    return {
        "city": cities.most_common(1)[0][0] if cities else None,
        "state": states.most_common(1)[0][0] if states else None,
    }


# ---------------------------------------------------------------------------
# Vertical classification via HuggingFace zero-shot
# ---------------------------------------------------------------------------

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import pipeline
        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )
    return _classifier


def classify_vertical(page_text: str, verticals: list[str]) -> str | None:
    """Classify *page_text* into one of *verticals* using zero-shot classification.

    Returns the highest-confidence label, or ``None`` on any failure.
    """
    try:
        clf = _get_classifier()
    except (ImportError, OSError) as exc:
        logger.debug("zero-shot model unavailable: %s", exc)
        return None

    try:
        result = clf(page_text[:1000], candidate_labels=verticals)
        return result["labels"][0]
    except Exception as exc:
        logger.warning("classify_vertical failed: %s", exc)
        return None
