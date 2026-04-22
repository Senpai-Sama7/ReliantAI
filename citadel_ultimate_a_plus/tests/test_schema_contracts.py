from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest


def _load_schemas(root: Path) -> dict[str, dict]:
    out = {}
    for p in (root / "schemas").glob("*.json"):
        out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
    return out


def test_schemas_are_valid(project_root: Path) -> None:
    for schema in _load_schemas(project_root).values():
        jsonschema.Draft7Validator.check_schema(schema)


def test_build_manifest_accepts_local_file_uri(project_root: Path) -> None:
    schemas = _load_schemas(project_root)
    manifest = {
        "lead_slug": "acme-houston-examplecom",
        "build_dir": "/tmp/builds/acme",
        "entrypoint": "index.html",
        "artifacts": ["index.html", "styles.css", "app.js"],
        "qa_notes": "Static preview generated and file set written locally.",
        "preview_url": "file:///tmp/builds/acme/index.html",
        "lighthouse_estimate": {"performance": 90, "accessibility": 94, "best_practices": 96, "seo": 97},
        "size_bytes": 12345,
        "build_sha": "0123456789abcdef",
    }
    jsonschema.validate(manifest, schemas["build_manifest"], format_checker=jsonschema.FormatChecker())


def test_outreach_subject_rejects_newlines(project_root: Path) -> None:
    schemas = _load_schemas(project_root)
    payload = {
        "lead_slug": "acme-houston-examplecom",
        "channel": "email",
        "to_email": "ops@example.com",
        "subject": "Bad\nSubject",
        "preview_text": "Valid preview text line only",
        "body_text": "x" * 120,
        "body_html": "<p>" + ("x" * 60) + "</p>",
        "cta_url": "file:///tmp/site/index.html",
        "compliance_footer": "Sent by Test. Mailing address: Humble, TX. Reply stop to opt out.",
        "disclosures_included": True,
        "beat_audit": {
            "pattern_break": "x" * 20,
            "cost_of_inaction": "x" * 20,
            "belief_shift": "x" * 20,
            "mechanism": "x" * 20,
            "proof_unit": "x" * 20,
            "offer": "x" * 20,
            "action": "x" * 10,
        },
        "beat_compliance_warning": [],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schemas["outreach_output"], format_checker=jsonschema.FormatChecker())
