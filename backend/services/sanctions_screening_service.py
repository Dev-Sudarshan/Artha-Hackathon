"""
OpenSanctions AML/CFT & PEP Screening Service
Uses the OpenSanctions Match API to check individuals against:
  - Global sanctions lists (OFAC, EU, UN, etc.)
  - Politically Exposed Persons (PEP) databases
  - Counter-Financing of Terrorism (CFT) watchlists
  - Criminal / enforcement lists

API Docs: https://www.opensanctions.org/docs/api/matching/
"""

import os
import requests
import logging

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
OPENSANCTIONS_API_KEY = os.getenv(
    "OPENSANCTIONS_API_KEY",
    "d41898595e1bca62925fa0a220fd9686",
)
OPENSANCTIONS_URL = os.getenv(
    "OPENSANCTIONS_URL",
    "https://api.opensanctions.org/match/default",
)

# Score threshold: matches above this are considered a positive hit (0-100 scale)
PEP_SCORE_THRESHOLD = float(os.getenv("PEP_SCORE_THRESHOLD", "0.50"))
SANCTIONS_SCORE_THRESHOLD = float(os.getenv("SANCTIONS_SCORE_THRESHOLD", "0.50"))

# Topics that indicate PEP
PEP_TOPICS = {"role.pep", "role.rca", "poi"}
# Topics that indicate sanctions / CFT
SANCTIONS_TOPICS = {"sanction", "debarment", "crime", "crime.fin", "crime.terror"}


def screen_individual(
    full_name: str,
    id_number: str = None,
    date_of_birth: str = None,
    nationality: str = "Nepal",
) -> dict:
    """
    Screen an individual against OpenSanctions for PEP, sanctions, and CFT.

    Args:
        full_name:      Full name of the person (e.g. "Ram Bahadur Thapa")
        id_number:       National ID / citizenship number (optional)
        date_of_birth:  Date of birth in any format (optional, e.g. "1990-01-15")
        nationality:    Country (default "Nepal")

    Returns:
        {
            "screened": True/False,          # whether screening was performed
            "is_pep": True/False,            # Politically Exposed Person
            "is_sanctioned": True/False,     # On sanctions / CFT list
            "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
            "total_matches": int,
            "pep_matches": [...],            # list of PEP match details
            "sanctions_matches": [...],      # list of sanctions match details
            "all_matches": [...],            # all raw matches
            "error": None or str
        }
    """
    result = {
        "screened": False,
        "is_pep": False,
        "is_sanctioned": False,
        "risk_level": "LOW",
        "total_matches": 0,
        "pep_matches": [],
        "sanctions_matches": [],
        "all_matches": [],
        "error": None,
    }

    if not full_name or not full_name.strip():
        result["error"] = "No name provided for screening"
        return result

    # ── Build the FtM entity ─────────────────────────────────────────────
    name_parts = full_name.strip().split()
    properties = {}

    if len(name_parts) == 1:
        properties["name"] = [full_name.strip()]
    else:
        properties["firstName"] = [name_parts[0]]
        properties["lastName"] = [name_parts[-1]]
        if len(name_parts) > 2:
            properties["fatherName"] = [" ".join(name_parts[1:-1])]

    if date_of_birth:
        properties["birthDate"] = [date_of_birth]

    if nationality:
        properties["nationality"] = [nationality]

    if id_number:
        properties["idNumber"] = [str(id_number)]

    query_entity = {
        "schema": "Person",
        "properties": properties,
    }

    batch_payload = {
        "queries": {
            "kyc_check": query_entity,
        }
    }

    # ── Call API ─────────────────────────────────────────────────────────
    try:
        logger.info(f"[SANCTIONS] Screening: {full_name} (ID: {id_number})")
        session = requests.Session()
        session.headers["Authorization"] = f"ApiKey {OPENSANCTIONS_API_KEY}"

        response = session.post(
            OPENSANCTIONS_URL,
            json=batch_payload,
            params={"algorithm": "best"},
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()
        responses = data.get("responses", {})
        check_result = responses.get("kyc_check", {})
        matches = check_result.get("results", [])

        result["screened"] = True
        result["total_matches"] = len(matches)

        # ── Classify each match ──────────────────────────────────────────
        for match in matches:
            score = match.get("score", 0)
            topics = set(match.get("properties", {}).get("topics", []))
            entity_id = match.get("id", "")
            caption = match.get("caption", "")
            datasets = match.get("datasets", [])
            match_schema = match.get("schema", "")
            props = match.get("properties", {})

            match_info = {
                "entity_id": entity_id,
                "name": caption,
                "score": round(score, 3),
                "topics": list(topics),
                "datasets": datasets,
                "schema": match_schema,
                "country": props.get("country", []),
                "birth_date": props.get("birthDate", []),
                "position": props.get("position", []),
                "notes": props.get("notes", []),
            }

            result["all_matches"].append(match_info)

            # Check PEP
            if topics & PEP_TOPICS and score >= PEP_SCORE_THRESHOLD:
                match_info["match_type"] = "PEP"
                result["pep_matches"].append(match_info)
                result["is_pep"] = True

            # Check Sanctions / CFT
            if topics & SANCTIONS_TOPICS and score >= SANCTIONS_SCORE_THRESHOLD:
                match_info["match_type"] = "SANCTIONS/CFT"
                result["sanctions_matches"].append(match_info)
                result["is_sanctioned"] = True

        # ── Determine risk level ─────────────────────────────────────────
        if result["is_sanctioned"]:
            result["risk_level"] = "CRITICAL"
        elif result["is_pep"]:
            # PEP with high score
            max_pep_score = max(
                (m["score"] for m in result["pep_matches"]), default=0
            )
            result["risk_level"] = "HIGH" if max_pep_score >= 0.7 else "MEDIUM"
        elif result["total_matches"] > 0:
            max_score = max(
                (m.get("score", 0) for m in result["all_matches"]), default=0
            )
            if max_score >= 0.5:
                result["risk_level"] = "MEDIUM"
            else:
                result["risk_level"] = "LOW"

        logger.info(
            f"[SANCTIONS] Result for {full_name}: "
            f"PEP={result['is_pep']}, Sanctioned={result['is_sanctioned']}, "
            f"Risk={result['risk_level']}, Matches={result['total_matches']}"
        )

    except requests.exceptions.Timeout:
        logger.warning("[SANCTIONS] OpenSanctions API timed out")
        result["error"] = "Screening service timed out"
    except requests.exceptions.HTTPError as e:
        logger.error(f"[SANCTIONS] API HTTP error: {e}")
        result["error"] = f"Screening API error: {e.response.status_code}"
    except Exception as e:
        logger.error(f"[SANCTIONS] Screening failed: {e}")
        result["error"] = f"Screening failed: {str(e)}"

    return result
