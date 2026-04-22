"""Tests for inference.py — ML location extraction and vertical classification."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# extract_location tests
# ---------------------------------------------------------------------------

def test_extract_location_returns_city_state(monkeypatch):
    """When spaCy model is available, extract city/state from clear text."""
    import inference
    monkeypatch.setattr(inference, "_nlp", None)  # reset cache

    # Build a mock spaCy doc with GPE entities
    ent_houston = MagicMock()
    ent_houston.label_ = "GPE"
    ent_houston.text = "Houston"

    ent_tx = MagicMock()
    ent_tx.label_ = "GPE"
    ent_tx.text = "TX"

    mock_doc = MagicMock()
    mock_doc.ents = [ent_houston, ent_tx]

    mock_nlp = MagicMock(return_value=mock_doc)

    with patch.object(inference, "_get_nlp", return_value=mock_nlp):
        result = inference.extract_location(["Located in Houston, TX"])

    assert result["city"] == "Houston"
    assert result["state"] == "TX"


def test_extract_location_returns_none_for_ambiguous(monkeypatch):
    """When no GPE entities found, return Nones."""
    import inference
    monkeypatch.setattr(inference, "_nlp", None)

    mock_doc = MagicMock()
    mock_doc.ents = []
    mock_nlp = MagicMock(return_value=mock_doc)

    with patch.object(inference, "_get_nlp", return_value=mock_nlp):
        result = inference.extract_location(["Some random text with no location"])

    assert result["city"] is None
    assert result["state"] is None


def test_extract_location_handles_missing_model(monkeypatch):
    """When spaCy model is not installed, return Nones gracefully."""
    import inference
    monkeypatch.setattr(inference, "_nlp", None)

    with patch.object(inference, "_get_nlp", side_effect=OSError("model not found")):
        result = inference.extract_location(["Located in Houston, TX"])

    assert result == {"city": None, "state": None}


# ---------------------------------------------------------------------------
# classify_vertical tests
# ---------------------------------------------------------------------------

def test_classify_vertical_returns_correct_label(monkeypatch):
    """When model is available, return highest-confidence label."""
    import inference
    monkeypatch.setattr(inference, "_classifier", None)

    mock_clf = MagicMock(return_value={"labels": ["plumbing", "hvac"], "scores": [0.9, 0.1]})

    with patch.object(inference, "_get_classifier", return_value=mock_clf):
        result = inference.classify_vertical("We fix pipes and drains", ["plumbing", "hvac"])

    assert result == "plumbing"


def test_classify_vertical_returns_none_on_import_error(monkeypatch):
    """When transformers/torch not installed, return None."""
    import inference
    monkeypatch.setattr(inference, "_classifier", None)

    with patch.object(inference, "_get_classifier", side_effect=ImportError("No module named 'torch'")):
        result = inference.classify_vertical("We fix pipes", ["plumbing", "hvac"])

    assert result is None


def test_classify_vertical_returns_none_on_os_error(monkeypatch):
    """When model download fails, return None."""
    import inference
    monkeypatch.setattr(inference, "_classifier", None)

    with patch.object(inference, "_get_classifier", side_effect=OSError("model not found")):
        result = inference.classify_vertical("We fix pipes", ["plumbing", "hvac"])

    assert result is None
