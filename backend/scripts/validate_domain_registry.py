#!/usr/bin/env python3
"""Validate the canonical domain ownership registry.

The registry is an architecture-spine file, not a service migration counter.
It must describe the same seven canonical domains that exist under
``backend/app/domains`` and it must keep the industry-standard code vocabulary
(``domains``) distinct from BijMantra's product vocabulary (``LOKA``).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install backend dependencies with `uv sync --extra dev`.")
    sys.exit(1)


EXPECTED_DOMAINS = ("sristi", "bijkosha", "rupa", "kshetra", "medha", "vani", "vidya")
EXPECTED_LAYERS = ("domain", "application", "ports", "schemas", "adapters")
EXPECTED_CAPABILITY_OWNERS = ("shared_kernel", *EXPECTED_DOMAINS, "standards_spine")
FORBIDDEN_DOMAIN_KEYS = {"bija_kosha", "bij_kosha", "bija-kosha", "bij-kosha"}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssertionError(f"Registry file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise AssertionError("Registry root must be a mapping")
    return data


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise AssertionError(f"`{key}` must be a mapping")
    return value


def _validate_architecture(registry: dict[str, Any]) -> None:
    architecture = _require_mapping(registry, "architecture")
    expected_type = "domain_bounded_modular_monolith_with_hexagonal_architecture"
    if architecture.get("type") != expected_type:
        raise AssertionError(f"architecture.type must be {expected_type!r}")
    if architecture.get("code_surface") != "backend/app/domains":
        raise AssertionError("architecture.code_surface must be backend/app/domains")
    if architecture.get("code_vocabulary") != "domain":
        raise AssertionError("architecture.code_vocabulary must be domain")
    if architecture.get("product_vocabulary") != "LOKA":
        raise AssertionError("architecture.product_vocabulary must be LOKA")
    if architecture.get("migration_rule") != "wrap_extract_drain":
        raise AssertionError("architecture.migration_rule must be wrap_extract_drain")


def _validate_domains(registry: dict[str, Any], domains_root: Path) -> None:
    domains = _require_mapping(registry, "domains")
    found = tuple(domains)
    if found != EXPECTED_DOMAINS:
        raise AssertionError(f"domains must be ordered as {EXPECTED_DOMAINS!r}; found {found!r}")
    forbidden_present = FORBIDDEN_DOMAIN_KEYS.intersection(domains)
    if forbidden_present:
        raise AssertionError(f"legacy Bijkosha aliases cannot be canonical keys: {sorted(forbidden_present)}")

    for domain_name in EXPECTED_DOMAINS:
        domain_config = domains.get(domain_name)
        if not isinstance(domain_config, dict):
            raise AssertionError(f"domain {domain_name!r} must be a mapping")
        owns = domain_config.get("owns")
        if not isinstance(owns, list) or not owns:
            raise AssertionError(f"domain {domain_name!r} must declare non-empty owns list")

        domain_root = domains_root / domain_name
        if not domain_root.exists():
            raise AssertionError(f"missing domain package: {domain_root}")
        for layer_name in EXPECTED_LAYERS:
            layer_root = domain_root / layer_name
            if not layer_root.exists():
                raise AssertionError(f"missing {domain_name}/{layer_name} layer")


def _validate_table_seed(registry: dict[str, Any]) -> None:
    table_seed = _require_mapping(registry, "table_ownership_seed")
    if table_seed.get("status") != "initial_not_exhaustive":
        raise AssertionError("table_ownership_seed.status must be initial_not_exhaustive")
    for owner in ("shared_kernel", *EXPECTED_DOMAINS):
        tables = table_seed.get(owner)
        if not isinstance(tables, list) or not tables:
            raise AssertionError(f"table_ownership_seed.{owner} must list at least one table")


def _validate_capability_layer(registry: dict[str, Any]) -> None:
    capability_layer = _require_mapping(registry, "capability_layer")
    if capability_layer.get("status") != "required_for_large_domain_growth":
        raise AssertionError("capability_layer.status must be required_for_large_domain_growth")
    if "domain -> capability -> hexagonal slice" not in capability_layer.get("rule", ""):
        raise AssertionError("capability_layer.rule must include the domain -> capability -> hexagonal slice rule")

    capability_inventory = _require_mapping(registry, "capability_inventory")
    if capability_inventory.get("status") != "initial_not_exhaustive":
        raise AssertionError("capability_inventory.status must be initial_not_exhaustive")
    for owner in EXPECTED_CAPABILITY_OWNERS:
        capabilities = capability_inventory.get(owner)
        if not isinstance(capabilities, list) or not capabilities:
            raise AssertionError(f"capability_inventory.{owner} must list at least one capability")


def main() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    registry_path = backend_dir / "app" / "domain_registry.yaml"
    domains_root = backend_dir / "app" / "domains"

    print("Validating canonical domain registry...")
    registry = _load_yaml(registry_path)
    _validate_architecture(registry)
    _validate_domains(registry, domains_root)
    _validate_capability_layer(registry)
    _validate_table_seed(registry)
    print("Domain registry is valid.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"Domain registry validation failed: {exc}")
        sys.exit(1)
