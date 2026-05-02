import os
import re

def is_conflict_marker(line):
    # Pattern: strictly start with <<<<<<<, =======, >>>>>>> 
    # But ignore if it's a comment like # ======= which is common in this codebase
    stripped = line.strip()
    return (
        stripped.startswith("<<<<<<<") or
        stripped.startswith("=======") or
        stripped.startswith(">>>>>>>")
    ) and not stripped.startswith("#") and not stripped.startswith("//")

def scan_file(filepath):
    with open(filepath, 'r') as f:
        try:
            lines = f.readlines()
        except UnicodeDecodeError:
            return False

    has_conflict = False
    for i, line in enumerate(lines):
        if is_conflict_marker(line):
            print(f"CONFLICT: {filepath}:{i+1}: {line.strip()}")
            has_conflict = True
    return has_conflict

target_files = [
    "backend/app/services/ai/engine.py",
    "backend/app/services/gxe_analysis.py",
    "backend/app/services/chaitanya/orchestrator.py",
    "backend/app/services/variety_licensing.py",
    "backend/app/services/rakshaka/anomaly_detector.py",
    "backend/app/services/rakshaka/health_monitor.py",
    "backend/app/services/rakshaka/healer.py",
    "backend/app/services/voice_service.py",
    "backend/app/services/seed_inventory.py",
    "backend/app/services/vision_model.py",
    "backend/app/services/trial_planning.py",
    "backend/app/services/seed_traceability.py"
]

print("Scanning for conflicts...")
for rel_path in target_files:
    abs_path = os.path.abspath(rel_path)
    if os.path.exists(abs_path):
        scan_file(abs_path)
    else:
        print(f"MISSING: {abs_path}")
