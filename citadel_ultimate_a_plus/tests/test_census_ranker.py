from __future__ import annotations

import json
from pathlib import Path

import pytest

from market.census_ranker import _validate_target_config


def test_valid_config(project_root: Path) -> None:
    cfg = json.loads((project_root / "market" / "target_verticals.json").read_text())
    _validate_target_config(cfg)


def test_missing_required_keys() -> None:
    with pytest.raises(ValueError, match="missing keys"):
        _validate_target_config({"verticals": [{"slug": "a", "naics": "1"}]})


def test_duplicate_slug() -> None:
    cfg = {"state_fips": "48", "county_fips": "201", "cbp_year": "2021", "verticals": [
        {"slug": "a", "naics": "1"}, {"slug": "a", "naics": "2"},
    ]}
    with pytest.raises(ValueError, match="duplicate"):
        _validate_target_config(cfg)


def test_split_ratio_exceeds_one() -> None:
    cfg = {"state_fips": "48", "county_fips": "201", "cbp_year": "2021", "verticals": [
        {"slug": "a", "naics": "1", "split_ratio": 0.7},
        {"slug": "b", "naics": "1", "split_ratio": 0.7},
    ]}
    with pytest.raises(ValueError, match="split_ratio sum exceeds"):
        _validate_target_config(cfg)


def test_empty_verticals() -> None:
    cfg = {"state_fips": "48", "county_fips": "201", "cbp_year": "2021", "verticals": []}
    with pytest.raises(ValueError, match="non-empty"):
        _validate_target_config(cfg)
