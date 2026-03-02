#!/usr/bin/env python3
"""
Update metrics.json script - Auto-generates metrics.json from codebase state
"""
import json
import os
import glob
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent.absolute()
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_DIR = ROOT_DIR / "backend" / "app"

METRICS_FILE = ROOT_DIR / "metrics.json"
KIRO_METRICS_FILE = ROOT_DIR / ".kiro" / "metrics.json"

def count_pages():
    pages_dir = FRONTEND_DIR / "src" / "pages"
    if not pages_dir.exists():
        return 0, 0, 0
    
    total_pages: int = 0
    demo_pages: int = 0
    for root, _, files in os.walk(pages_dir):
        for f in files:
            if f.endswith(".tsx") or f.endswith(".jsx"):
                total_pages += 1
                try:
                    content = open(os.path.join(root, f), 'r').read()
                    if "DEMO_" in content or "mock" in content.lower():
                        demo_pages += 1
                except Exception:
                    pass
    return total_pages, total_pages - demo_pages, demo_pages

def get_bundle_size():
    dist_dir = FRONTEND_DIR / "dist"
    if not dist_dir.exists():
        return 0, "0.0MB"
    
    total_size = sum(f.stat().st_size for f in dist_dir.glob('**/*') if f.is_file())
    return int(total_size / 1024), f"{total_size / (1024 * 1024):.1f}MB"

def count_endpoints():
    routers_dir = BACKEND_DIR / "api"
    if not routers_dir.exists():
        return 0, 0
    total: int = 0
    brapi: int = 0
    for file in routers_dir.rglob("*.py"):
        try:
            content = open(file, 'r').read()
            methods = ["@router.get", "@router.post", "@router.put", "@router.delete", "@router.patch"]
            for line in content.split('\n'):
                for m in methods:
                    if m in line:
                        total += 1
                        if "brapi" in str(file) or "brapi" in line:
                            brapi += 1
        except Exception:
            pass
    return total, brapi

def main():
    print("Gathering metrics data...")
    
    total_pages, functional_pages, demo_pages = count_pages()
    total_endpoints, brapi_endpoints = count_endpoints()
    bundle_kb, bundle_mb = get_bundle_size()
    
    # Load existing metrics to preserve some structure
    old_metrics: dict = {}
    if METRICS_FILE.exists():
        with open(METRICS_FILE, 'r') as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                old_metrics = loaded
                
    def get_dict(d: dict, key: str) -> dict:
        val = d.get(key, {})
        return val if isinstance(val, dict) else {}
            
    metrics = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "updatedBy": "Automated metrics script",
        "session": old_metrics.get("session", 0),
        "pages": {
            "total": total_pages if total_pages > 0 else get_dict(old_metrics, "pages").get("total", 0),
            "functional": functional_pages if total_pages > 0 else get_dict(old_metrics, "pages").get("functional", 0),
            "demo": demo_pages,
            "uiOnly": get_dict(old_metrics, "pages").get("uiOnly", 0),
            "removed": get_dict(old_metrics, "pages").get("removed", 0)
        },
        "api": {
            "totalEndpoints": total_endpoints if total_endpoints > 0 else get_dict(old_metrics, "api").get("totalEndpoints", 0),
            "brapiEndpoints": brapi_endpoints if brapi_endpoints > 0 else get_dict(old_metrics, "api").get("brapiEndpoints", 0),
            "brapiCoverage": min(100, int((brapi_endpoints / 201) * 100)) if brapi_endpoints > 0 else get_dict(old_metrics, "api").get("brapiCoverage", 0),
            "customEndpoints": total_endpoints - brapi_endpoints if total_endpoints > 0 else get_dict(old_metrics, "api").get("customEndpoints", 0)
        },
        "database": old_metrics.get("database", {}),
        "modules": old_metrics.get("modules", {}),
        "workspaces": old_metrics.get("workspaces", {}),
        "build": {
            "status": get_dict(old_metrics, "build").get("status", "passing"),
            "pwaEntries": get_dict(old_metrics, "build").get("pwaEntries", 0),
            "sizeKB": bundle_kb if bundle_kb > 0 else get_dict(old_metrics, "build").get("sizeKB", 0),
            "sizeMB": bundle_mb if bundle_kb > 0 else get_dict(old_metrics, "build").get("sizeMB", "0MB")
        },
        "milestones": old_metrics.get("milestones", {}),
        "techStack": old_metrics.get("techStack", {}),
        "version": old_metrics.get("version", {"app": "0.2.0", "brapi": "2.1", "schema": "1.0.0"}),
        "tests": old_metrics.get("tests", {})
    }
    
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Updated {METRICS_FILE}")
    
    # Save to kiro too if it exists
    if KIRO_METRICS_FILE.parent.exists():
        with open(KIRO_METRICS_FILE, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ Updated {KIRO_METRICS_FILE}")

if __name__ == "__main__":
    main()
