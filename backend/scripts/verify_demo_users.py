#!/usr/bin/env python3
"""
Verification script for Task 8: Demo user access and credential isolation.

Checks:
  8.1 - demo@bijmantra.org, breeder@bijmantra.org, researcher@bijmantra.org all exist
        with organization_id pointing to Demo Organization (Requirements 13.1–13.3)
  8.2 - Demo user passwords are stored as bcrypt hashes (not plaintext) (Requirement 13.5)
  8.3 - After `make db-seed-clear`, admin@bijmantra.org still exists and
        ReferenceDataSeeder is isolated (is_demo_data=False, not cleared by demo scope)
        (Requirements 14.1–14.5)

Usage:
    cd backend && uv run python scripts/verify_demo_users.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Ensure the backend package is importable when run from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_db_session():
    """Create a synchronous DB session using the same approach as seed.py."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def check_81_demo_users_in_demo_org(db) -> bool:
    """
    8.1 — Confirm demo@bijmantra.org, breeder@bijmantra.org, and researcher@bijmantra.org
    all exist with organization_id pointing to Demo Organization.
    Requirements: 13.1–13.3
    """
    from app.core.demo_dataset import DEMO_DATASET_ORG_NAME
    from app.models.core import Organization, User

    print("\n── 8.1  Demo users exist in Demo Organization ──────────────────────────")

    demo_org = (
        db.query(Organization)
        .filter(Organization.name == DEMO_DATASET_ORG_NAME)
        .first()
    )
    if demo_org is None:
        print(f"  ✗  Demo Organization '{DEMO_DATASET_ORG_NAME}' not found in database.")
        print("     Run `make db-seed` first.")
        return False

    print(f"  ✓  Demo Organization found: id={demo_org.id!r}, name={demo_org.name!r}")

    expected_emails = [
        "demo@bijmantra.org",
        "breeder@bijmantra.org",
        "researcher@bijmantra.org",
    ]

    all_ok = True
    for email in expected_emails:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            print(f"  ✗  User not found: {email}")
            all_ok = False
        elif user.organization_id != demo_org.id:
            print(
                f"  ✗  {email} exists but organization_id={user.organization_id!r} "
                f"(expected {demo_org.id!r})"
            )
            all_ok = False
        else:
            print(
                f"  ✓  {email}  →  organization_id={user.organization_id!r} "
                f"(matches Demo Organization)"
            )

    return all_ok


def check_82_passwords_are_bcrypt(db) -> bool:
    """
    8.2 — Confirm demo user passwords are stored as bcrypt hashes (not plaintext).
    bcrypt hashes always start with '$2b$'.
    Requirement: 13.5
    """
    from app.models.core import User

    print("\n── 8.2  Demo user passwords are bcrypt hashes ──────────────────────────")

    demo_emails = [
        "demo@bijmantra.org",
        "breeder@bijmantra.org",
        "researcher@bijmantra.org",
    ]

    all_ok = True
    for email in demo_emails:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            print(f"  ✗  User not found: {email}  (run `make db-seed` first)")
            all_ok = False
            continue

        hp = user.hashed_password or ""
        if hp.startswith("$2b$"):
            print(f"  ✓  {email}  →  hashed_password starts with '$2b$' (bcrypt)")
        else:
            prefix = hp[:10] if hp else "(empty)"
            print(
                f"  ✗  {email}  →  hashed_password does NOT start with '$2b$' "
                f"(got: {prefix!r}...)"
            )
            all_ok = False

    return all_ok


def run_db_seed_clear() -> bool:
    """Run `make db-seed-clear` from the repo root and return True on success."""
    repo_root = Path(__file__).parent.parent.parent
    print("\n── Running `make db-seed-clear` ────────────────────────────────────────")
    result = subprocess.run(
        ["make", "db-seed-clear"],
        cwd=str(repo_root),
        capture_output=False,  # let output stream to terminal
    )
    if result.returncode != 0:
        print(f"\n  ✗  `make db-seed-clear` exited with code {result.returncode}")
        return False
    print("  ✓  `make db-seed-clear` completed successfully")
    return True


def check_83_system_seeders_untouched(db) -> bool:
    """
    8.3 — After `make db-seed-clear`:
      • admin@bijmantra.org still exists in the users table (AdminUserSeeder not cleared)
      • ReferenceDataSeeder.is_demo_data == False (static isolation property)
      • ReferenceDataSeeder is NOT in the demo-scope clear list (registry isolation)
    Requirements: 14.1–14.5
    """
    from app.models.core import User

    print("\n── 8.3  System seeder data untouched after db-seed-clear ───────────────")

    all_ok = True

    # ── DB check: admin user must still exist ─────────────────────────────
    admin = db.query(User).filter(User.email == "admin@bijmantra.org").first()
    if admin is None:
        print("  ✗  admin@bijmantra.org NOT found — AdminUserSeeder data was cleared!")
        all_ok = False
    else:
        print(f"  ✓  admin@bijmantra.org still exists (id={admin.id!r})")

    # ── Static check: ReferenceDataSeeder.is_demo_data must be False ──────
    import app.db.seeders  # noqa: F401 — trigger registration
    from app.db.seeders.base import get_all_seeders
    from app.db.seeders.reference_data import ReferenceDataSeeder

    if ReferenceDataSeeder.is_demo_data is False:
        print("  ✓  ReferenceDataSeeder.is_demo_data == False (system seeder)")
    else:
        print("  ✗  ReferenceDataSeeder.is_demo_data is not False!")
        all_ok = False

    # ── Registry check: ReferenceDataSeeder must NOT appear in demo scope ─
    all_seeders = get_all_seeders()
    demo_seeders = [s for s in all_seeders if getattr(s, "is_demo_data", True)]
    system_seeders = [s for s in all_seeders if not getattr(s, "is_demo_data", True)]

    ref_in_demo = any(s.name == "reference_data" for s in demo_seeders)
    ref_in_system = any(s.name == "reference_data" for s in system_seeders)

    if ref_in_demo:
        print("  ✗  reference_data seeder appears in demo scope — it would be cleared!")
        all_ok = False
    else:
        print("  ✓  reference_data seeder is NOT in demo scope (will not be cleared by db-seed-clear)")

    if ref_in_system:
        print("  ✓  reference_data seeder is correctly registered in system scope")
    else:
        print("  ⚠  reference_data seeder not found in system scope (check registration)")

    # ── AdminUserSeeder isolation check ───────────────────────────────────
    admin_in_demo = any(s.name == "admin_user" for s in demo_seeders)
    if admin_in_demo:
        print("  ✗  admin_user seeder appears in demo scope — it would be cleared!")
        all_ok = False
    else:
        print("  ✓  admin_user seeder is NOT in demo scope (will not be cleared by db-seed-clear)")

    # ── Confirm demo users are gone (clear worked correctly) ──────────────
    demo_emails = [
        "demo@bijmantra.org",
        "breeder@bijmantra.org",
        "researcher@bijmantra.org",
    ]
    remaining_demo_users = (
        db.query(User).filter(User.email.in_(demo_emails)).count()
    )
    if remaining_demo_users == 0:
        print("  ✓  All demo users removed by db-seed-clear (as expected)")
    else:
        print(
            f"  ⚠  {remaining_demo_users} demo user(s) still present after clear "
            f"(may be intentional if clear was partial)"
        )

    return all_ok


def main() -> int:
    print("=" * 70)
    print("  Task 8: Demo User Access and Credential Isolation Verification")
    print("=" * 70)

    results: dict[str, bool] = {}

    # ── 8.1 and 8.2 — require demo data to be seeded ──────────────────────
    db = get_db_session()
    try:
        results["8.1"] = check_81_demo_users_in_demo_org(db)
        results["8.2"] = check_82_passwords_are_bcrypt(db)
    finally:
        db.close()

    # ── 8.3 — run clear, then re-check system seeder isolation ────────────
    clear_ok = run_db_seed_clear()
    if not clear_ok:
        print("\n  ✗  Skipping 8.3 checks because db-seed-clear failed.")
        results["8.3"] = False
    else:
        # Re-open session after clear so we see the post-clear state
        db = get_db_session()
        try:
            results["8.3"] = check_83_system_seeders_untouched(db)
        finally:
            db.close()

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    all_passed = True
    for task_id, passed in results.items():
        status = "✓  PASS" if passed else "✗  FAIL"
        print(f"  {status}  Task {task_id}")
        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("  All checks passed.\n")
        return 0
    else:
        print("  One or more checks FAILED. See details above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
