import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "insureai.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the local INSUREAI SQLite database.
    """

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALISE DATABASE
# ============================================================

def initialise_database() -> None:
    """
    Create the company profile cache table if it does not
    already exist.
    """

    with get_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS company_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                company_key TEXT NOT NULL UNIQUE,
                profile_json TEXT NOT NULL,
                researched_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.commit()


# ============================================================
# READ COMPANY PROFILE
# ============================================================

def get_company_profile(
    company_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Return a previously researched company profile from SQLite.

    Company names are normalised so searches such as
    'Amazon' and ' amazon ' use the same cached record.
    """

    company_key = company_name.strip().lower()

    if not company_key:
        return None

    initialise_database()

    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT
                profile_json,
                researched_at,
                updated_at
            FROM company_profiles
            WHERE company_key = ?
            """,
            (company_key,),
        ).fetchone()

    if row is None:
        return None

    profile = json.loads(
        row["profile_json"]
    )

    profile["_cache"] = {
        "hit": True,
        "researched_at": row["researched_at"],
        "updated_at": row["updated_at"],
    }

    return profile


# ============================================================
# SAVE / UPDATE COMPANY PROFILE
# ============================================================

def save_company_profile(
    company_name: str,
    profile: Dict[str, Any],
) -> None:
    """
    Store a researched company profile.

    If the company already exists, its profile is updated
    instead of creating a duplicate record.
    """

    cleaned_name = company_name.strip()

    if not cleaned_name:
        raise ValueError(
            "Company name cannot be empty."
        )

    company_key = cleaned_name.lower()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    initialise_database()

    profile_json = json.dumps(
        profile,
        ensure_ascii=False,
    )

    with get_connection() as connection:

        existing = connection.execute(
            """
            SELECT researched_at
            FROM company_profiles
            WHERE company_key = ?
            """,
            (company_key,),
        ).fetchone()

        researched_at = (
            existing["researched_at"]
            if existing
            else now
        )

        connection.execute(
            """
            INSERT INTO company_profiles (
                company_name,
                company_key,
                profile_json,
                researched_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(company_key)
            DO UPDATE SET
                company_name = excluded.company_name,
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at
            """,
            (
                cleaned_name,
                company_key,
                profile_json,
                researched_at,
                now,
            ),
        )

        connection.commit()