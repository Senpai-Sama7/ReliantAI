"""
HVAC LEAD GENERATOR - Composio SDK Version

This version uses the Composio SDK plus connected Google Maps and Google
Sheets accounts instead of direct provider API keys.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from composio import Composio, ComposioToolSet
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_ACTION = "GOOGLE_MAPS_TEXT_SEARCH"
GOOGLE_SHEETS_LIST_ACTION = "GOOGLESHEETS_GET_SHEET_NAMES"
GOOGLE_SHEETS_ADD_ACTION = "GOOGLESHEETS_ADD_SHEET"
GOOGLE_SHEETS_WRITE_ACTION = "GOOGLESHEETS_BATCH_UPDATE"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate HVAC leads with Composio-backed Google Maps and Sheets.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and format leads, but do not write a new Google Sheet tab.",
    )
    parser.add_argument(
        "--profile-locations",
        action="store_true",
        help="Profile the configured locations and show how many candidates match before writing anything.",
    )
    parser.add_argument(
        "--output-json",
        help="Write a JSON artifact of the run result to the provided path.",
    )
    return parser.parse_args()


def now() -> str:
    return datetime.now().isoformat()


def is_missing(value: str | None) -> bool:
    if value is None:
        return True
    stripped = value.strip()
    if not stripped:
        return True
    lowered = stripped.lower()
    return lowered.startswith("your_") or lowered.endswith("_here") or "placeholder" in lowered


def get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if is_missing(value):
        raise RuntimeError(f"{name} must be set to a real value before running.")
    return value


def get_sheet_id() -> str:
    sheet_id = os.environ.get("google_sheet_id", "").strip()
    if not is_missing(sheet_id):
        return sheet_id

    sheet_url = os.environ.get("google_sheet_url", "").strip()
    if not is_missing(sheet_url) and "docs.google.com" in sheet_url:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
        if match:
            return match.group(1)

    raise RuntimeError("Set google_sheet_id (preferred) or a valid google_sheet_url in .env before running.")


def create_toolset() -> ComposioToolSet:
    api_key = get_required_env("COMPOSIO_API_KEY")
    entity_id = get_entity_id()
    return ComposioToolSet(api_key=api_key, entity_id=entity_id)


def get_entity_id() -> str:
    return os.environ.get("COMPOSIO_ENTITY_ID", "default").strip() or "default"


def create_composio_client() -> Composio:
    return Composio(api_key=get_required_env("COMPOSIO_API_KEY"))


def build_missing_connection_error(toolset: ComposioToolSet, action: str, exc: Exception) -> RuntimeError:
    action_model = toolset.get_action(action)
    app_name = action_model.appName
    entity_id = get_entity_id()
    entity = create_composio_client().get_entity(entity_id)
    connection_request = entity.initiate_connection(app_name.lower(), force_new_integration=False)
    return RuntimeError(
        f"Missing connected account for {app_name}. "
        f"Complete the auth flow here: {connection_request.redirectUrl} "
        f"and then retry with COMPOSIO_ENTITY_ID={entity_id}."
    )


def get_missing_connection_message(toolset: ComposioToolSet, action: str) -> str | None:
    try:
        action_model = toolset.get_action(action)
        entity = create_composio_client().get_entity(get_entity_id())
        entity.get_connection(app=action_model.appName.lower())
        return None
    except Exception as exc:
        return str(build_missing_connection_error(toolset, action, exc))


def ensure_connection(toolset: ComposioToolSet, action: str) -> None:
    message = get_missing_connection_message(toolset, action)
    if message:
        raise RuntimeError(message)


def is_connection_error(exc: Exception) -> bool:
    message = str(exc)
    return "No connected account" in message or "Could not find a connection" in message


def get_retry_settings() -> tuple[int, float]:
    max_retries = max(1, int(os.environ.get("COMPOSIO_MAX_RETRIES", "3")))
    base_delay = max(0.25, float(os.environ.get("COMPOSIO_RETRY_BASE_DELAY_SECONDS", "1.0")))
    return max_retries, base_delay


def execute_action(toolset: ComposioToolSet, action: str, params: dict[str, Any]) -> dict[str, Any]:
    max_retries, base_delay = get_retry_settings()
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = toolset.execute_action(action, params)
            if response.get("successful", False):
                return response.get("data", {})

            error_message = response.get("error") or f"{action} failed without an error message."
            if attempt == max_retries:
                raise RuntimeError(error_message)
            time.sleep(base_delay * (2 ** (attempt - 1)))
        except Exception as exc:
            if is_connection_error(exc):
                raise build_missing_connection_error(toolset, action, exc) from exc
            last_error = exc
            if attempt == max_retries:
                break
            time.sleep(base_delay * (2 ** (attempt - 1)))

    if last_error is not None:
        raise RuntimeError(f"{action} failed after {max_retries} attempts: {last_error}") from last_error
    raise RuntimeError(f"{action} failed after {max_retries} attempts without a successful response.")


def build_rows(leads: list[dict[str, Any]]) -> list[list[str]]:
    headers = [
        "Company Name",
        "Phone",
        "Email",
        "Address",
        "Rating",
        "Review Count",
        "Years in Business",
        "Services",
        "Specialties",
        "Service Area",
        "Unique Selling Points",
        "Google Maps URL",
        "Research Sources",
        "Location Searched",
        "Date Added",
    ]
    rows: list[list[str]] = [headers]

    for lead in leads:
        rows.append(
            [
                lead.get("name", ""),
                lead.get("phone", ""),
                lead.get("email", "Not found"),
                lead.get("address", ""),
                str(lead.get("rating", "")),
                str(lead.get("review_count", "")),
                lead.get("years_in_business", "Unknown"),
                lead.get("services_offered", "Unknown"),
                lead.get("specialties", ""),
                lead.get("service_area", "Unknown"),
                lead.get("unique_selling_points", ""),
                lead.get("google_maps_url", ""),
                lead.get("research_sources", ""),
                lead.get("location", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    return rows


def fetch_places(
    toolset: ComposioToolSet,
    location: str,
    max_result_count: int,
) -> list[dict[str, Any]]:
    payload = {
        "textQuery": f"HVAC companies in {location}",
        "maxResultCount": min(max_result_count, 20),
        "fieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.nationalPhoneNumber,places.websiteUri,places.rating,"
            "places.userRatingCount,places.googleMapsUri"
        ),
    }

    data = execute_action(toolset, GOOGLE_MAPS_ACTION, payload)
    return data.get("places", [])


def search_location(
    toolset: ComposioToolSet,
    location: str,
    min_rating: float,
    min_review_count: int,
    max_result_count: int,
) -> list[dict[str, Any]]:
    places = fetch_places(toolset, location, max_result_count)
    leads: list[dict[str, Any]] = []

    for place in places:
        rating = float(place.get("rating", 0) or 0)
        review_count = int(place.get("userRatingCount", 0) or 0)
        website = place.get("websiteUri", "")

        if rating >= min_rating and review_count >= min_review_count and not website:
            leads.append(
                {
                    "name": (place.get("displayName") or {}).get("text", ""),
                    "phone": place.get("nationalPhoneNumber", ""),
                    "email": "Not found",
                    "address": place.get("formattedAddress", ""),
                    "rating": rating,
                    "review_count": review_count,
                    "years_in_business": "Unknown",
                    "services_offered": "Unknown",
                    "specialties": "",
                    "service_area": "Unknown",
                    "unique_selling_points": "",
                    "google_maps_url": place.get("googleMapsUri", ""),
                    "research_sources": "",
                    "location": location,
                }
            )

    return leads


def profile_location(
    toolset: ComposioToolSet,
    location: str,
    min_rating: float,
    min_review_count: int,
    max_result_count: int,
) -> dict[str, Any]:
    places = fetch_places(toolset, location, max_result_count)
    no_website = [place for place in places if not place.get("websiteUri", "")]
    qualified = [
        place
        for place in no_website
        if float(place.get("rating", 0) or 0) >= min_rating
        and int(place.get("userRatingCount", 0) or 0) >= min_review_count
    ]
    sample = [
        {
            "name": (place.get("displayName") or {}).get("text", ""),
            "rating": place.get("rating", 0),
            "review_count": place.get("userRatingCount", 0),
            "address": place.get("formattedAddress", ""),
        }
        for place in qualified[:3]
    ]
    return {
        "location": location,
        "places_found": len(places),
        "without_website": len(no_website),
        "qualified": len(qualified),
        "sample": sample,
    }


def dedupe_leads(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for lead in leads:
        key = (lead.get("name", ""), lead.get("address", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(lead)
    return unique


def ensure_sheet_and_write(
    toolset: ComposioToolSet,
    spreadsheet_id: str,
    rows: list[list[str]],
) -> str:
    sheets_data = execute_action(toolset, GOOGLE_SHEETS_LIST_ACTION, {"spreadsheet_id": spreadsheet_id})
    sheet_names = sheets_data.get("sheet_names", [])

    sheet_name = f"HVAC_Leads_{datetime.now().strftime('%Y%m%d_%H%M')}"
    if sheet_name in sheet_names:
        sheet_name = f"{sheet_name}_{datetime.now().strftime('%S')}"

    execute_action(
        toolset,
        GOOGLE_SHEETS_ADD_ACTION,
        {
            "spreadsheetId": spreadsheet_id,
            "properties": {
                "title": sheet_name,
                "gridProperties": {
                    "rowCount": len(rows) + 10,
                    "columnCount": len(rows[0]) if rows else 15,
                    "frozenRowCount": 1,
                },
            },
        },
    )

    execute_action(
        toolset,
        GOOGLE_SHEETS_WRITE_ACTION,
        {
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "values": rows,
            "first_cell_location": "A1",
            "valueInputOption": "USER_ENTERED",
        },
    )

    return sheet_name


def load_runtime_config() -> dict[str, Any]:
    return {
        "target_locations": [
            item.strip()
            for item in os.environ.get(
                "target_locations",
                "Springfield, IL;Peoria, IL;Rockford, IL;Bloomington, IL;Decatur, IL;Tyler, TX;Shreveport, LA;Mobile, AL",
            ).split(";")
            if item.strip()
        ],
        "min_rating": float(os.environ.get("min_rating", "3.5")),
        "min_review_count": int(os.environ.get("min_review_count", "5")),
        "results_per_location": int(os.environ.get("results_per_location", "20")),
    }


def print_profile_summary(profiles: list[dict[str, Any]]) -> None:
    print(f"[{now()}] Location profile summary")
    for profile in profiles:
        print(
            f"- {profile['location']}: "
            f"{profile['qualified']} qualified / "
            f"{profile['without_website']} without website / "
            f"{profile['places_found']} total"
        )
        for sample in profile["sample"]:
            print(
                f"  sample: {sample['name']} | "
                f"rating={sample['rating']} | "
                f"reviews={sample['review_count']} | "
                f"{sample['address']}"
            )


def write_output_json(path_value: str, payload: dict[str, Any]) -> None:
    output_path = Path(path_value).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = load_runtime_config()
    target_locations = config["target_locations"]
    min_rating = config["min_rating"]
    min_review_count = config["min_review_count"]
    results_per_location = config["results_per_location"]

    toolset = create_toolset()
    required_actions = [GOOGLE_MAPS_ACTION]
    if not args.dry_run and not args.profile_locations:
        required_actions.append(GOOGLE_SHEETS_WRITE_ACTION)
    missing_connections = [message for message in [get_missing_connection_message(toolset, action) for action in required_actions] if message]
    if missing_connections:
        raise RuntimeError("Missing required connections:\n- " + "\n- ".join(missing_connections))

    if args.profile_locations:
        profiles = [
            profile_location(toolset, location, min_rating, min_review_count, results_per_location)
            for location in target_locations
        ]
        profile_output = {
            "mode": "profile",
            "generated_at": now(),
            "config": config,
            "profiles": profiles,
        }
        if args.output_json:
            write_output_json(args.output_json, profile_output)
        print_profile_summary(profiles)
        return

    print(f"[{now()}] Starting HVAC Lead Generator")
    print(f"  Target locations: {len(target_locations)}")
    print(f"  Min rating: {min_rating}")
    print(f"  Min reviews: {min_review_count}")
    print(f"  Results per location: {results_per_location}")

    print(f"\n[{now()}] STEP 1: Searching for HVAC companies")
    leads: list[dict[str, Any]] = []

    max_workers = min(5, max(1, len(target_locations)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                search_location,
                toolset,
                location,
                min_rating,
                min_review_count,
                results_per_location,
            )
            for location in target_locations
        ]
        for future in as_completed(futures):
            location_leads = future.result()
            leads.extend(location_leads)

    leads = dedupe_leads(leads)
    print(f"  Found {len(leads)} total leads without websites")

    print(f"\n[{now()}] STEP 2: Formatting rows")
    rows = build_rows(leads)
    print(f"  Prepared {len(rows) - 1} lead rows")

    if args.dry_run:
        summary = {
            "mode": "dry-run",
            "generated_at": now(),
            "dry_run": True,
            "total_leads_found": len(leads),
            "locations_searched": target_locations,
            "filter_criteria": {
                "min_rating": min_rating,
                "min_reviews": min_review_count,
                "has_website": "No",
            },
            "output_json_path": args.output_json or None,
            "sample_leads": leads[:5],
            "leads": leads,
        }
        if args.output_json:
            write_output_json(args.output_json, summary)
        print("\n" + "=" * 80)
        print("DRY RUN COMPLETE")
        print("=" * 80)
        print(json.dumps(summary, indent=2))
        return

    print(f"\n[{now()}] STEP 3: Writing to Google Sheets")
    spreadsheet_id = get_sheet_id()
    sheet_name = ensure_sheet_and_write(toolset, spreadsheet_id, rows)

    summary = {
        "mode": "run",
        "generated_at": now(),
        "total_leads_found": len(leads),
        "sheet_name": sheet_name,
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
        "locations_searched": target_locations,
        "filter_criteria": {
            "min_rating": min_rating,
            "min_reviews": min_review_count,
            "has_website": "No",
        },
        "output_json_path": args.output_json or None,
        "leads": leads,
    }
    if args.output_json:
        write_output_json(args.output_json, summary)

    print("\n" + "=" * 80)
    print("LEAD GENERATION COMPLETE")
    print("=" * 80)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[{now()}] ERROR: {exc}")
        raise SystemExit(1)
