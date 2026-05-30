from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


DOMAIN_FILES = {
    "breeding": {
        "backend/app/models/core.py",
        "backend/app/models/germplasm.py",
    },
    "germplasm": {
        "backend/app/models/germplasm.py",
        "backend/app/modules/seed_bank/models.py",
    },
    "phenotyping": {
        "backend/app/models/phenotyping.py",
        "backend/app/models/phenomic.py",
        "backend/app/models/brapi_phenotyping.py",
    },
    "field_operations": {
        "backend/app/models/field_operations.py",
        "backend/app/models/environmental.py",
        "backend/app/models/iot.py",
    },
    "intelligence": {
        "backend/app/models/genotyping.py",
        "backend/app/modules/bio_analytics/models.py",
        "backend/app/models/qtl.py",
        "backend/app/models/biometrics.py",
    },
    "commercial": {
        "backend/app/models/economics.py",
        "backend/app/models/cost_analysis.py",
    },
    "knowledge": {
        "backend/app/models/social.py",
        "backend/app/models/collaboration.py",
    },
}

DOMAIN_DATA_NEEDS = {
    "breeding": {
        "description": "Breeding programs, locations, trials, studies, crosses, seedlots",
        "data_needs": {
            "trial_metadata": "BrAPI servers, CGIAR trial repositories, national AICRP-style trial portals",
            "pedigrees": "BrAPI, GENESYS, crop publications",
            "locations": "GeoNames, Wikidata, national agricultural station registries",
        },
    },
    "germplasm": {
        "description": "Germplasm and seed-bank conservation records",
        "data_needs": {
            "taxonomy": "GBIF, GRIN Taxonomy, Crop Ontology",
            "accessions": "GENESYS, USDA GRIN-Global, CGIAR genebanks",
            "viability": "seed-bank protocols plus synthetic edge-case augmentation",
        },
    },
    "phenotyping": {
        "description": "Traits, observation variables, observation units, observations, samples, images",
        "data_needs": {
            "traits": "Crop Ontology, MIAPPE, BrAPI variables",
            "observations": "BrAPI test servers, CGIAR datasets, FAOSTAT yield series",
            "methods": "Crop Ontology methods and scales, ISA-Tab/MIAPPE metadata",
        },
    },
    "field_operations": {
        "description": "Field operations, nursery, environmental units, soil profiles",
        "data_needs": {
            "weather": "NASA POWER, Open-Meteo, national weather portals",
            "soil": "SoilGrids, ISRIC, NBSS&LUP references",
            "field_books": "BrAPI field books, Field Book app exports, synthetic plot layouts",
        },
    },
    "intelligence": {
        "description": "Genomics, GWAS, QTLs, candidate genes, breeding values",
        "data_needs": {
            "references": "Ensembl Plants, NCBI Assembly, Gramene",
            "variants": "1001 Genomes, 3K Rice Genomes, CIMMYT/Cornell datasets",
            "qtl_gwas": "Gramene QTL, QTARO, GWAS Catalog, crop publications",
        },
    },
    "commercial": {
        "description": "Economics, cost-benefit, and market trends",
        "data_needs": {
            "production": "FAOSTAT, World Bank, national agriculture portals",
            "prices": "World Bank Pink Sheet, Agmarknet, commodity exchange data",
            "costs": "government cost-of-cultivation datasets and synthetic budgets",
        },
    },
    "knowledge": {
        "description": "Social knowledge, reputation, posts, groups, collaboration",
        "data_needs": {
            "knowledge": "internal training content and public extension advisories",
            "community": "synthetic tenant-safe demo conversations",
            "moderation": "synthetic safety and reporting edge cases",
        },
    },
}


def discover_schema(repo_root: Path) -> dict[str, Any]:
    model_files = sorted((repo_root / "backend" / "app" / "models").glob("*.py"))
    model_files.extend(sorted((repo_root / "backend" / "app" / "modules").glob("*/models.py")))

    tables: dict[str, dict[str, Any]] = {}
    enums: dict[str, list[str]] = {}
    relationships: list[dict[str, str]] = []

    for file_path in model_files:
        relative = file_path.relative_to(repo_root).as_posix()
        parsed = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        file_enums = _extract_enums(parsed)
        enums.update(file_enums)
        for class_node in [node for node in parsed.body if isinstance(node, ast.ClassDef)]:
            table_name = _extract_table_name(class_node)
            if not table_name:
                continue
            columns, class_relationships = _extract_columns_and_relationships(class_node)
            tables[table_name] = {
                "model": class_node.name,
                "file": relative,
                "columns": columns,
                "foreign_keys": [
                    {"column": name, "target": data["foreign_key"]}
                    for name, data in columns.items()
                    if data.get("foreign_key")
                ],
                "relationships": class_relationships,
                "implicit_base_fields": _implicit_base_fields(class_node),
            }
            for rel in class_relationships:
                relationships.append({"table": table_name, **rel})

    domains = {
        domain: {
            "tables": sorted(
                table_name
                for table_name, table in tables.items()
                if table["file"] in files
            ),
            **DOMAIN_DATA_NEEDS[domain],
        }
        for domain, files in DOMAIN_FILES.items()
    }

    return {
        "generated_by": "data_pipeline.discovery.schema_discovery",
        "metrics": {
            "model_count": len(tables),
            "table_count": len(tables),
            "relationship_count": len(relationships),
        },
        "domains": domains,
        "tables": tables,
        "enums": enums,
    }


def _extract_table_name(class_node: ast.ClassDef) -> str | None:
    for statement in class_node.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name) and target.id == "__tablename__":
                    return _literal_string(statement.value)
    return None


def _extract_enums(parsed: ast.Module) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for node in parsed.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_expr_name(base).endswith("StrEnum") or _expr_name(base).endswith("Enum") for base in node.bases):
            continue
        values: list[str] = []
        for statement in node.body:
            if isinstance(statement, ast.Assign):
                literal = _literal_string(statement.value)
                if literal is not None:
                    values.append(literal)
        if values:
            result[node.name] = values
    return result


def _extract_columns_and_relationships(
    class_node: ast.ClassDef,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    columns: dict[str, dict[str, Any]] = {}
    relationships: list[dict[str, str]] = []
    for statement in class_node.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if _is_call_named(statement.value, "Column"):
            columns[target.id] = _column_metadata(statement.value)
        elif _is_call_named(statement.value, "relationship"):
            relationships.append(
                {
                    "name": target.id,
                    "target": _relationship_target(statement.value),
                }
            )
    return columns, relationships


def _column_metadata(call: ast.Call) -> dict[str, Any]:
    foreign_key = None
    type_name = "Unknown"
    for arg in call.args:
        if _is_call_named(arg, "ForeignKey"):
            foreign_key = _literal_string(arg.args[0]) if arg.args else None
            continue
        if _is_call_named(arg, "SQLEnum") or _is_call_named(arg, "Enum"):
            type_name = f"Enum[{_expr_name(arg.args[0]) if arg.args else 'Unknown'}]"
            continue
        if type_name == "Unknown":
            type_name = _expr_name(arg)
    kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}
    nullable = _literal_bool(kwargs.get("nullable"))
    primary_key = _literal_bool(kwargs.get("primary_key")) is True
    return {
        "type": type_name,
        "foreign_key": foreign_key,
        "required": primary_key or nullable is False,
        "nullable": True if nullable is None else nullable,
        "primary_key": primary_key,
        "unique": _literal_bool(kwargs.get("unique")) is True,
        "indexed": _literal_bool(kwargs.get("index")) is True,
        "default": _expr_name(kwargs["default"]) if "default" in kwargs else None,
    }


def _relationship_target(call: ast.Call) -> str:
    if call.args:
        literal = _literal_string(call.args[0])
        if literal:
            return literal
        return _expr_name(call.args[0])
    return "Unknown"


def _implicit_base_fields(class_node: ast.ClassDef) -> list[str]:
    base_names = {_expr_name(base) for base in class_node.bases}
    if "BaseModel" in base_names:
        return ["id", "created_at", "updated_at"]
    return []


def _is_call_named(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Call) and _expr_name(node.func).split(".")[-1] == name


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _literal_bool(node: ast.AST | None) -> bool | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return None


def _expr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_expr_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _expr_name(node.func)
    if isinstance(node, ast.Subscript):
        return _expr_name(node.value)
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return node.__class__.__name__

