"""
Data Export Service for Plant Breeding
Export data in various formats (CSV, JSON, Excel-compatible)

Features:
- Trial data export
- Phenotype data export
- Pedigree data export
- Custom query export
- BrAPI-compatible export
"""

import csv
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class ExportConfig:
    """Export configuration"""
    format: str  # csv, json, tsv
    include_headers: bool = True
    date_format: str = "%Y-%m-%d"
    null_value: str = ""
    delimiter: str = ","


class DataExportService:
    """
    Data export service for plant breeding data
    """

    def __init__(self):
        pass

    def export_to_csv(
        self,
        data: list[dict[str, Any]],
        columns: list[str] | None = None,
        include_headers: bool = True
    ) -> str:
        """
        Export data to CSV format

        Args:
            data: List of dictionaries
            columns: Column order (None = auto-detect)
            include_headers: Include header row

        Returns:
            CSV string
        """
        if not data:
            return ""

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        output = io.StringIO()
        writer = csv.writer(output)

        if include_headers:
            writer.writerow(columns)

        for row in data:
            writer.writerow([self._format_value(row.get(col, "")) for col in columns])

        return output.getvalue()

    def export_to_tsv(
        self,
        data: list[dict[str, Any]],
        columns: list[str] | None = None,
        include_headers: bool = True
    ) -> str:
        """Export data to TSV format"""
        if not data:
            return ""

        if columns is None:
            columns = list(data[0].keys())

        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')

        if include_headers:
            writer.writerow(columns)

        for row in data:
            writer.writerow([self._format_value(row.get(col, "")) for col in columns])

        return output.getvalue()

    def export_to_json(
        self,
        data: list[dict[str, Any]],
        pretty: bool = True
    ) -> str:
        """Export data to JSON format"""
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    def _format_value(self, value: Any) -> str:
        """Format a value for export"""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return str(value)

    def export_trial_data(
        self,
        trial_id: str,
        observations: list[dict[str, Any]],
        format: str = "csv"
    ) -> dict[str, Any]:
        """
        Export trial observation data

        Standard columns: plot_id, genotype, block, rep, trait, value, date
        """
        # Flatten observations if nested
        flat_data = []
        for obs in observations:
            flat_data.append({
                "trial_id": trial_id,
                "plot_id": obs.get("plot_id", ""),
                "genotype": obs.get("genotype", ""),
                "block": obs.get("block", ""),
                "rep": obs.get("rep", ""),
                "trait": obs.get("trait", ""),
                "value": obs.get("value", ""),
                "unit": obs.get("unit", ""),
                "date": obs.get("date", ""),
                "observer": obs.get("observer", ""),
            })

        columns = ["trial_id", "plot_id", "genotype", "block", "rep",
                   "trait", "value", "unit", "date", "observer"]

        if format == "csv":
            content = self.export_to_csv(flat_data, columns)
        elif format == "tsv":
            content = self.export_to_tsv(flat_data, columns)
        else:
            content = self.export_to_json(flat_data)

        return {
            "trial_id": trial_id,
            "format": format,
            "row_count": len(flat_data),
            "columns": columns,
            "content": content,
            "filename": f"trial_{trial_id}_{datetime.now().strftime('%Y%m%d')}.{format}",
        }

    def export_phenotype_matrix(
        self,
        genotypes: list[str],
        traits: list[str],
        values: dict[str, dict[str, Any]],  # genotype -> trait -> value
        format: str = "csv"
    ) -> dict[str, Any]:
        """
        Export phenotype data as genotype × trait matrix

        Rows = genotypes, Columns = traits
        """
        data = []
        for geno in genotypes:
            row = {"genotype": geno}
            for trait in traits:
                row[trait] = values.get(geno, {}).get(trait, "")
            data.append(row)

        columns = ["genotype"] + traits

        if format == "csv":
            content = self.export_to_csv(data, columns)
        elif format == "tsv":
            content = self.export_to_tsv(data, columns)
        else:
            content = self.export_to_json(data)

        return {
            "format": format,
            "n_genotypes": len(genotypes),
            "n_traits": len(traits),
            "columns": columns,
            "content": content,
            "filename": f"phenotype_matrix_{datetime.now().strftime('%Y%m%d')}.{format}",
        }

    def export_pedigree(
        self,
        pedigree_data: list[dict[str, Any]],
        format: str = "csv"
    ) -> dict[str, Any]:
        """
        Export pedigree data

        Standard columns: id, sire, dam, generation, inbreeding
        """
        columns = ["id", "sire", "dam", "generation", "inbreeding_coefficient"]

        data = []
        for ind in pedigree_data:
            data.append({
                "id": ind.get("id", ""),
                "sire": ind.get("sire_id", ind.get("sire", "")),
                "dam": ind.get("dam_id", ind.get("dam", "")),
                "generation": ind.get("generation", ""),
                "inbreeding_coefficient": ind.get("inbreeding_coefficient", ind.get("inbreeding", "")),
            })

        if format == "csv":
            content = self.export_to_csv(data, columns)
        elif format == "tsv":
            content = self.export_to_tsv(data, columns)
        else:
            content = self.export_to_json(data)

        return {
            "format": format,
            "n_individuals": len(data),
            "columns": columns,
            "content": content,
            "filename": f"pedigree_{datetime.now().strftime('%Y%m%d')}.{format}",
        }

    def export_marker_data(
        self,
        genotypes: list[str],
        markers: list[str],
        calls: dict[str, dict[str, str]],  # genotype -> marker -> call
        format: str = "csv"
    ) -> dict[str, Any]:
        """
        Export marker genotype data

        Rows = genotypes, Columns = markers
        """
        data = []
        for geno in genotypes:
            row = {"genotype": geno}
            for marker in markers:
                row[marker] = calls.get(geno, {}).get(marker, "")
            data.append(row)

        columns = ["genotype"] + markers

        if format == "csv":
            content = self.export_to_csv(data, columns)
        elif format == "tsv":
            content = self.export_to_tsv(data, columns)
        else:
            content = self.export_to_json(data)

        return {
            "format": format,
            "n_genotypes": len(genotypes),
            "n_markers": len(markers),
            "columns": columns,
            "content": content,
            "filename": f"marker_data_{datetime.now().strftime('%Y%m%d')}.{format}",
        }

    def export_brapi_germplasm(
        self,
        germplasm_list: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Export germplasm in BrAPI format
        """
        brapi_data = {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": 0,
                    "pageSize": len(germplasm_list),
                    "totalCount": len(germplasm_list),
                    "totalPages": 1,
                },
                "status": [{"message": "Success", "messageType": "INFO"}],
            },
            "result": {
                "data": germplasm_list,
            },
        }

        return {
            "format": "brapi_json",
            "n_records": len(germplasm_list),
            "content": json.dumps(brapi_data, indent=2),
            "filename": f"germplasm_brapi_{datetime.now().strftime('%Y%m%d')}.json",
        }

    def generate_field_book(
        self,
        trial_id: str,
        plots: list[dict[str, Any]],
        traits: list[str],
        format: str = "csv"
    ) -> dict[str, Any]:
        """
        Generate field book template for data collection

        Creates a template with plot info and empty columns for traits.
        """
        data = []
        for plot in plots:
            row = {
                "trial_id": trial_id,
                "plot_id": plot.get("plot_id", ""),
                "row": plot.get("row", ""),
                "column": plot.get("column", ""),
                "block": plot.get("block", ""),
                "genotype": plot.get("genotype", ""),
            }
            # Add empty trait columns
            for trait in traits:
                row[trait] = ""
            data.append(row)

        columns = ["trial_id", "plot_id", "row", "column", "block", "genotype"] + traits

        if format == "csv":
            content = self.export_to_csv(data, columns)
        elif format == "tsv":
            content = self.export_to_tsv(data, columns)
        else:
            content = self.export_to_json(data)

        return {
            "trial_id": trial_id,
            "format": format,
            "n_plots": len(plots),
            "traits": traits,
            "columns": columns,
            "content": content,
            "filename": f"fieldbook_{trial_id}_{datetime.now().strftime('%Y%m%d')}.{format}",
        }


# Singleton
_export_service: DataExportService | None = None


def get_export_service() -> DataExportService:
    """Get or create export service singleton"""
    global _export_service
    if _export_service is None:
        _export_service = DataExportService()
    return _export_service
