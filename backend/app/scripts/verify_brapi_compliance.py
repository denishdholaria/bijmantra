"""Check BrAPI endpoint count and required baseline paths from static route scan."""

from __future__ import annotations

from app.scripts.generate_api_docs import _extract_routes


REQUIRED_BASICS = {("GET", "/brapi/v2/serverinfo")}
MIN_BRAPI_OPERATIONS = 201


def main() -> int:
    routes = _extract_routes()
    brapi = {(item["method"], item["path"]) for item in routes if item["path"].startswith("/brapi/v2")}

    missing = sorted(REQUIRED_BASICS - brapi)
    if missing:
        print(f"Missing required BrAPI operations: {missing}")
        return 1

    if len(brapi) < MIN_BRAPI_OPERATIONS:
        print(f"BrAPI operations below target: {len(brapi)} < {MIN_BRAPI_OPERATIONS}")
        return 1

    print(f"BrAPI compliance verified for {len(brapi)} operations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
