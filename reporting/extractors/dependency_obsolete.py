# reporting/extractors/dependency.py
"""Extractor for cycles, include paths, and unresolved imports."""
from __future__ import annotations
from typing import Dict, List, Any
from .base import IInsightExtractor, InsightRecord, TraceabilityRecord

class DependencyExtractor(IInsightExtractor):
    @property
    def extractor_id(self) -> str: return "dependency"
    @property
    def default_thresholds(self) -> Dict[str, Any]:
        return {"cycles_allowed": 0, "unresolved_import_warn": 5}

    def collect_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        edges = raw_data.get("edges", [])
        include_paths = [e for e in edges if e.get("relation") == "imports"]
        return {
            "all_include_paths": include_paths,
            "circular_dependencies": raw_data.get("aggregated_metrics", {}).get("circular_dependencies", []),
            "unresolved_count": sum(1 for e in include_paths if e.get("confidence") != "EXTRACTED")
        }

    def extract(self, raw_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]:
        insights = []
        cfg = {**self.default_thresholds, **thresholds}
        metrics = raw_data.get("aggregated_metrics", {})
        edges = raw_data.get("edges", [])

        cycles = metrics.get("circular_dependencies", [])
        if len(cycles) > cfg["cycles_allowed"]:
            insights.append(InsightRecord("INS-CYCL-001", "dependency_coupling", "critical",
                "Circular Import Chain Detected", f"Found {len(cycles)} cycle(s) blocking isolation.",
                [c[0] for c in cycles[:5]], [TraceabilityRecord("circular_dependencies", len(cycles), cfg["cycles_allowed"], "FAIL", "aggregated_metrics.circular_dependencies")],
                "Break cycles via interfaces, event buses, or lazy imports.", self.extractor_id))

        unresolved = sum(1 for e in edges if e.get("relation") == "imports" and e.get("confidence") != "EXTRACTED")
        if unresolved > cfg["unresolved_import_warn"]:
            insights.append(InsightRecord("INS-UNRES-001", "reference_integrity", "warning",
                "High Rate of Unresolved Imports", f"{unresolved} imports not resolved to physical files.",
                ["edge_trace"], [TraceabilityRecord("unresolved_imports", unresolved, cfg["unresolved_import_warn"], "WARN", "edges[*].confidence")],
                "Verify sys.path, venv config, or update import regex patterns.", self.extractor_id))
        return insights