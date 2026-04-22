#!/usr/bin/env python3
"""
Pull Census County Business Patterns (CBP) establishment counts and convert them
into density weights used by the qualifier stage.
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import time
from pathlib import Path
from typing import Optional

import requests

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
OUT_PATH = ROOT / "market_weights.json"

log = logging.getLogger("citadel.market.census_ranker")


def fetch_establishments(
    naics: str,
    state_fips: str,
    county_fips: str,
    cbp_year: str,
    *,
    session: Optional[requests.Session] = None,
    api_key: Optional[str] = None,
) -> int:
    """
    Census CBP endpoint shape:
      /data/{year}/cbp?get=ESTAB,NAICS2017&for=county:XXX&in=state:YY&NAICS2017=...
    We request total establishments with LFO=001 and EMPSZES=001.
    """
    base_url = f"https://api.census.gov/data/{cbp_year}/cbp"
    params = {
        "get": "ESTAB,NAICS2017",
        "for": f"county:{county_fips}",
        "in": f"state:{state_fips}",
        "NAICS2017": naics,
        "LFO": "001",
        "EMPSZES": "001",
    }
    if api_key:
        params["key"] = api_key

    http = session or requests.Session()
    last_exc: Optional[Exception] = None
    for attempt in range(5):
        try:
            resp = http.get(base_url, params=params, timeout=20)
            resp.raise_for_status()
            rows = resp.json()
            if not isinstance(rows, list) or len(rows) < 2:
                return 0
            header = rows[0]
            first_row = rows[1]
            if not isinstance(header, list) or not isinstance(first_row, list):
                return 0
            mapped = dict(zip(header, first_row))
            return int(mapped.get("ESTAB", 0))
        except Exception as exc:
            last_exc = exc
            wait = (2 ** attempt) + random.random()
            log.warning("fetch failed for NAICS=%s attempt=%s: %s (retry %.1fs)", naics, attempt + 1, exc, wait)
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch Census CBP for NAICS {naics}: {last_exc}")


def _validate_target_config(cfg: dict) -> None:
    required = {"state_fips", "county_fips", "cbp_year", "verticals"}
    missing = required - set(cfg)
    if missing:
        raise ValueError(f"target config missing keys: {sorted(missing)}")
    if not isinstance(cfg["verticals"], list) or not cfg["verticals"]:
        raise ValueError("target config 'verticals' must be a non-empty list")
    seen = set()
    ratio_by_naics: dict[str, float] = {}
    for row in cfg["verticals"]:
        for key in ("slug", "naics"):
            if key not in row:
                raise ValueError(f"vertical missing {key}: {row}")
        slug = row["slug"]
        if slug in seen:
            raise ValueError(f"duplicate vertical slug: {slug}")
        seen.add(slug)
        ratio = float(row.get("split_ratio", 1.0))
        if ratio <= 0:
            raise ValueError(f"split_ratio must be positive for {slug}")
        row["split_ratio"] = ratio
        ratio_by_naics[row["naics"]] = ratio_by_naics.get(row["naics"], 0.0) + ratio
    over = {k: v for k, v in ratio_by_naics.items() if v > 1.00001}
    if over:
        raise ValueError(f"split_ratio sum exceeds 1.0 for shared NAICS codes: {over}")


def run_ranker(config_path: Optional[Path] = None, api_key: Optional[str] = None) -> dict:
    cfg_path = (config_path or ROOT / "target_verticals.json").resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    _validate_target_config(cfg)

    session = requests.Session()
    naics_totals: dict[str, int] = {}
    for vertical in cfg["verticals"]:
        code = vertical["naics"]
        if code not in naics_totals:
            naics_totals[code] = fetch_establishments(
                code,
                cfg["state_fips"],
                cfg["county_fips"],
                str(cfg["cbp_year"]),
                session=session,
                api_key=api_key,
            )

    counts: dict[str, int] = {}
    for vertical in cfg["verticals"]:
        slug = vertical["slug"]
        code = vertical["naics"]
        ratio = float(vertical.get("split_ratio", 1.0))
        counts[slug] = int(round(naics_totals[code] * ratio))

    vals = list(counts.values()) or [0]
    lo, hi = min(vals), max(vals)
    spread = (hi - lo) or 1

    out = {
        "_meta": {
            "state_fips": cfg["state_fips"],
            "county_fips": cfg["county_fips"],
            "cbp_year": str(cfg["cbp_year"]),
            "generated_at_epoch": int(time.time()),
        },
        "weights": {
            slug: {
                "establishments": count,
                "density_weight": round((count - lo) / spread, 4),
            }
            for slug, count in counts.items()
        },
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, default=ROOT / "target_verticals.json")
    p.add_argument("--api-key", default=None)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = run_ranker(args.config, args.api_key)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
