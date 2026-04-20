#!/usr/bin/env python3
"""Quick endpoint validation for pedigree graph API."""

import argparse
import json
import sys
from urllib import request, error


def main() -> int:
    parser = argparse.ArgumentParser(description="Test pedigree endpoint response structure")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--germplasm-id", required=True, help="Germplasm ID to query")
    parser.add_argument("--depth", type=int, default=2, help="Graph depth")
    parser.add_argument("--token", default=None, help="Bearer token for authenticated endpoint")
    args = parser.parse_args()

    url = f"{args.base_url}/api/v1/pedigree/{args.germplasm_id}?depth={args.depth}"
    req = request.Request(url)
    if args.token:
        req.add_header("Authorization", f"Bearer {args.token}")

    try:
        with request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        print(f"HTTPError: {exc.code} {exc.reason}")
        print(exc.read().decode("utf-8"))
        return 1
    except Exception as exc:
        print(f"Request failed: {exc}")
        return 1

    if not isinstance(payload, dict):
        print("Invalid response: not a JSON object")
        return 1

    required_top_level = {"success", "germplasm_id", "depth", "nodes", "edges"}
    missing = required_top_level - payload.keys()
    if missing:
        print(f"Missing keys: {sorted(missing)}")
        return 1

    if not isinstance(payload["nodes"], list) or not isinstance(payload["edges"], list):
        print("nodes/edges must be lists")
        return 1

    for node in payload["nodes"]:
        if "data" not in node or "id" not in node["data"]:
            print("Invalid node format")
            return 1

    for edge in payload["edges"]:
        if "data" not in edge or "source" not in edge["data"] or "target" not in edge["data"]:
            print("Invalid edge format")
            return 1

    print(f"OK: nodes={len(payload['nodes'])}, edges={len(payload['edges'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
