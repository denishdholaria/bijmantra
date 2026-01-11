"""
Field Scanner Service
Manages field scan results, plot analysis, and scan history
"""
from datetime import datetime, UTC, timedelta
from typing import Optional
from uuid import uuid4


class FieldScannerService:
    """Service for field scanning operations and scan result management."""

    def __init__(self):
        self._scans: dict[str, dict] = {}
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize demo scan data."""
        base_time = datetime.now(UTC) - timedelta(hours=2)
        
        demo_scans = [
            {
                "id": "scan-demo-001",
                "plot_id": "Plot-A1",
                "study_id": "study-001",
                "timestamp": (base_time + timedelta(minutes=10)).isoformat(),
                "location": {"lat": 28.6139, "lng": 77.2090},
                "crop": "rice",
                "results": [
                    {"type": "trait", "label": "Canopy Coverage", "confidence": 0.92, "value": 78, "unit": "%"},
                    {"type": "trait", "label": "Greenness Index", "confidence": 0.88, "value": 0.72, "unit": "index"},
                    {"type": "growth_stage", "label": "Tillering", "confidence": 0.85, "stage_code": "BBCH 25"},
                ],
                "thumbnail": None,
                "notes": "Healthy plot, good tillering",
                "weather": {"temp": 28, "humidity": 65, "conditions": "Partly cloudy"},
                "created_by": "demo@bijmantra.org",
            },
            {
                "id": "scan-demo-002",
                "plot_id": "Plot-A2",
                "study_id": "study-001",
                "timestamp": (base_time + timedelta(minutes=25)).isoformat(),
                "location": {"lat": 28.6140, "lng": 77.2092},
                "crop": "rice",
                "results": [
                    {"type": "disease", "label": "Bacterial Leaf Blight", "confidence": 0.78, "severity": "medium", "affected_area": 15},
                    {"type": "stress", "label": "Nutrient Stress", "confidence": 0.65, "severity": 35},
                    {"type": "trait", "label": "Canopy Coverage", "confidence": 0.90, "value": 62, "unit": "%"},
                ],
                "thumbnail": None,
                "notes": "Disease symptoms observed, needs treatment",
                "weather": {"temp": 29, "humidity": 62, "conditions": "Sunny"},
                "created_by": "demo@bijmantra.org",
            },
            {
                "id": "scan-demo-003",
                "plot_id": "Plot-B1",
                "study_id": "study-001",
                "timestamp": (base_time + timedelta(minutes=45)).isoformat(),
                "location": {"lat": 28.6142, "lng": 77.2088},
                "crop": "wheat",
                "results": [
                    {"type": "trait", "label": "Canopy Coverage", "confidence": 0.94, "value": 85, "unit": "%"},
                    {"type": "trait", "label": "LAI Estimate", "confidence": 0.82, "value": 4.2, "unit": "m²/m²"},
                    {"type": "growth_stage", "label": "Stem Elongation", "confidence": 0.88, "stage_code": "BBCH 32"},
                ],
                "thumbnail": None,
                "notes": "Excellent growth, no issues",
                "weather": {"temp": 27, "humidity": 68, "conditions": "Cloudy"},
                "created_by": "demo@bijmantra.org",
            },
            {
                "id": "scan-demo-004",
                "plot_id": "Plot-B2",
                "study_id": "study-001",
                "timestamp": (base_time + timedelta(minutes=60)).isoformat(),
                "location": {"lat": 28.6143, "lng": 77.2091},
                "crop": "wheat",
                "results": [
                    {"type": "stress", "label": "Drought Stress", "confidence": 0.72, "severity": 45},
                    {"type": "trait", "label": "Canopy Coverage", "confidence": 0.89, "value": 58, "unit": "%"},
                    {"type": "trait", "label": "Senescence Score", "confidence": 0.85, "value": 22, "unit": "%"},
                ],
                "thumbnail": None,
                "notes": "Drought stress visible, irrigation needed",
                "weather": {"temp": 31, "humidity": 45, "conditions": "Sunny"},
                "created_by": "demo@bijmantra.org",
            },
        ]
        
        for scan in demo_scans:
            self._scans[scan["id"]] = scan

    def get_scans(
        self,
        study_id: Optional[str] = None,
        plot_id: Optional[str] = None,
        crop: Optional[str] = None,
        has_issues: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get scan results with filters."""
        scans = list(self._scans.values())
        
        if study_id:
            scans = [s for s in scans if s.get("study_id") == study_id]
        if plot_id:
            scans = [s for s in scans if s.get("plot_id") == plot_id]
        if crop:
            scans = [s for s in scans if s.get("crop", "").lower() == crop.lower()]
        if has_issues is not None:
            if has_issues:
                scans = [s for s in scans if any(
                    r.get("type") in ["disease", "stress"] and r.get("confidence", 0) > 0.5
                    for r in s.get("results", [])
                )]
            else:
                scans = [s for s in scans if not any(
                    r.get("type") in ["disease", "stress"] and r.get("confidence", 0) > 0.5
                    for r in s.get("results", [])
                )]
        if start_date:
            scans = [s for s in scans if s.get("timestamp", "") >= start_date]
        if end_date:
            scans = [s for s in scans if s.get("timestamp", "") <= end_date]
        
        # Sort by timestamp descending
        scans.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        total = len(scans)
        scans = scans[offset:offset + limit]
        
        return {
            "scans": scans,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_scan(self, scan_id: str) -> Optional[dict]:
        """Get a single scan by ID."""
        return self._scans.get(scan_id)

    def create_scan(self, data: dict) -> dict:
        """Create a new scan result."""
        scan_id = data.get("id") or f"scan-{uuid4().hex[:8]}"
        
        scan = {
            "id": scan_id,
            "plot_id": data.get("plot_id", f"Plot-{len(self._scans) + 1}"),
            "study_id": data.get("study_id"),
            "timestamp": data.get("timestamp") or datetime.now(UTC).isoformat(),
            "location": data.get("location"),
            "crop": data.get("crop", "rice"),
            "results": data.get("results", []),
            "thumbnail": data.get("thumbnail"),
            "notes": data.get("notes", ""),
            "weather": data.get("weather"),
            "created_by": data.get("created_by", "system"),
        }
        
        self._scans[scan_id] = scan
        return scan

    def update_scan(self, scan_id: str, data: dict) -> Optional[dict]:
        """Update an existing scan."""
        if scan_id not in self._scans:
            return None
        
        scan = self._scans[scan_id]
        
        if "notes" in data:
            scan["notes"] = data["notes"]
        if "results" in data:
            scan["results"] = data["results"]
        if "plot_id" in data:
            scan["plot_id"] = data["plot_id"]
        
        return scan

    def delete_scan(self, scan_id: str) -> bool:
        """Delete a scan."""
        if scan_id in self._scans:
            del self._scans[scan_id]
            return True
        return False

    def get_stats(self, study_id: Optional[str] = None) -> dict:
        """Get scanning statistics."""
        scans = list(self._scans.values())
        
        if study_id:
            scans = [s for s in scans if s.get("study_id") == study_id]
        
        total_scans = len(scans)
        plots_scanned = len(set(s.get("plot_id") for s in scans))
        
        # Count issues
        issues_found = sum(1 for s in scans if any(
            r.get("type") in ["disease", "stress"] and r.get("confidence", 0) > 0.5
            for r in s.get("results", [])
        ))
        healthy_plots = total_scans - issues_found
        
        # Disease breakdown
        diseases = {}
        stresses = {}
        for scan in scans:
            for result in scan.get("results", []):
                if result.get("type") == "disease" and result.get("confidence", 0) > 0.5:
                    label = result.get("label", "Unknown")
                    diseases[label] = diseases.get(label, 0) + 1
                elif result.get("type") == "stress" and result.get("confidence", 0) > 0.5:
                    label = result.get("label", "Unknown")
                    stresses[label] = stresses.get(label, 0) + 1
        
        # Crop breakdown
        crops = {}
        for scan in scans:
            crop = scan.get("crop", "unknown")
            crops[crop] = crops.get(crop, 0) + 1
        
        return {
            "total_scans": total_scans,
            "plots_scanned": plots_scanned,
            "healthy_plots": healthy_plots,
            "issues_found": issues_found,
            "diseases": diseases,
            "stresses": stresses,
            "crops": crops,
            "last_scan": max((s.get("timestamp") for s in scans), default=None) if scans else None,
        }

    def get_plot_history(self, plot_id: str) -> list[dict]:
        """Get scan history for a specific plot."""
        scans = [s for s in self._scans.values() if s.get("plot_id") == plot_id]
        scans.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return scans

    def export_scans(self, study_id: Optional[str] = None, format: str = "json") -> dict:
        """Export scan data."""
        result = self.get_scans(study_id=study_id, limit=10000)
        scans = result["scans"]
        
        if format == "csv":
            # Return CSV-ready data
            rows = []
            for scan in scans:
                base = {
                    "scan_id": scan["id"],
                    "plot_id": scan["plot_id"],
                    "timestamp": scan["timestamp"],
                    "crop": scan.get("crop", ""),
                    "lat": scan.get("location", {}).get("lat") if scan.get("location") else None,
                    "lng": scan.get("location", {}).get("lng") if scan.get("location") else None,
                    "notes": scan.get("notes", ""),
                }
                # Flatten results
                for i, r in enumerate(scan.get("results", [])[:5]):
                    base[f"result_{i+1}_type"] = r.get("type", "")
                    base[f"result_{i+1}_label"] = r.get("label", "")
                    base[f"result_{i+1}_confidence"] = r.get("confidence", 0)
                rows.append(base)
            return {"format": "csv", "data": rows, "count": len(rows)}
        
        return {"format": "json", "data": scans, "count": len(scans)}


# Singleton instance
field_scanner_service = FieldScannerService()
