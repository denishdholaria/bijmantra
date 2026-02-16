import os
import sys
import subprocess
import importlib
import logging
from pathlib import Path
import time

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HealthCheck")

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_result(check_name, status, msg=""):
    color = GREEN if status == "PASS" else RED
    print(f"{color}[{status}] {check_name}{RESET} {msg}")

def check_imports():
    logger.info("Checking critical imports...")
    modules = [
        "app.main",
        "app.models.core",
        "app.models.germplasm",
        "app.models.mars",
        "app.api.v2.chat",
    ]
    failed = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception as e:
            failed.append(f"{mod}: {e}")

    if failed:
        print_result("Import Check", "FAIL", f"Failed to import: {failed}")
        return False
    print_result("Import Check", "PASS")
    return True

def check_migrations():
    logger.info("Checking Alembic migrations via subprocess...")
    try:
        # Use Alembic to check if we are current
        result = subprocess.run(
            ["venv/bin/alembic", "check"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True
        )

        # 'alembic check' returns 0 if all is well
        if result.returncode == 0:
            print_result("Migration Sync", "PASS", "Schema is up to date")
            return True
        else:
            # Fallback output check
            print_result("Migration Sync", "FAIL", "Database is not up-to-date")
            print(YELLOW + result.stdout + RESET)
            print(RED + result.stderr + RESET)
            return False

    except Exception as e:
        print_result("Migration Check", "FAIL", str(e))
        return False

def check_server_health(url="http://localhost:8000/health"):
    try:
        import requests
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
             print_result("Backend Server", "PASS", "Responding to /health")
             return True
        else:
             print_result("Backend Server", "FAIL", f"Status: {resp.status_code}")
             return False
    except ImportError:
        logger.warning("Requests not installed, skipping server check")
        return True
    except Exception as e:
        print_result("Backend Server", "FAIL", f"Connection failed: {e}")
        return False

def run_verification_scripts():
    logger.info("Running functional verification scripts...")
    scripts = [
        "scripts/verify_veena_chat.py",
        "scripts/verify_space.py"
    ]

    all_passed = True
    for script in scripts:
        script_path = BASE_DIR / script
        if not script_path.exists():
            print_result(f"Script {script}", "WARN", "File not found")
            continue

        logger.info(f"Executing {script}...")
        try:
            result = subprocess.run(
                ["venv/bin/python", str(script_path)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                 print_result(f"{script} Execution", "PASS")
            else:
                 print_result(f"{script} Execution", "FAIL", f"Exit Code: {result.returncode}")
                 print(YELLOW + "--- STDOUT ---" + RESET)
                 print(result.stdout)
                 print(RED + "--- STDERR ---" + RESET)
                 print(result.stderr)
                 all_passed = False
        except Exception as e:
            print_result(f"{script} Execution", "FAIL", str(e))
            all_passed = False

    return all_passed

def main():
    print("🚀 STARTING SYSTEM HEALTH CHECK ('The Comb Out')")
    print("==================================================")

    # 1. Check Imports (Code Integrity)
    imports_ok = check_imports()

    # 2. Check Migrations (DB Integrity)
    migrations_ok = check_migrations()

    # 3. Check Server (Runtime Integrity)
    server_ok = check_server_health()

    # 4. Functional Scripts
    scripts_ok = False
    if server_ok:
        scripts_ok = run_verification_scripts()
    else:
        print(f"{YELLOW}[SKIP] Skipping functional tests because server is down.{RESET}")

    print("==================================================")
    if imports_ok and migrations_ok and server_ok and scripts_ok:
        print(f"{GREEN}🎉 STATUS: GREEN LIGHT - SYSTEM NOMINAL{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}⚠️  STATUS: YELLOW/RED LIGHT - ISSUES DETECTED{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
