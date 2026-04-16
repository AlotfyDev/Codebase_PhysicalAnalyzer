# reporting/extractors/dependency.py
from typing import Dict, List, Any
from .base import BaseExtractor, TraceabilityRecord, InsightRecord

class DependencyExtractor(BaseExtractor):
    @property
    def extractor_id(self) -> str: return "dependency"
    @property
    def default_thresholds(self) -> dict: return {"cycles_allowed": 0, "unresolved_warn": 5}

    def get_raw_findings(self, raw_: Dict[str, Any]) -> Dict[str, Any]:
        return {"circular_deps": raw_.get("aggregated_metrics", {}).get("circular_dependencies", [])}

    def _extract_impl(self, raw_: Dict[str, Any], cfg: Dict[str, Any]) -> List[InsightRecord]:
        insights = []
        cycles = raw_.get("aggregated_metrics", {}).get("circular_dependencies", [])
        if len(cycles) > cfg["cycles_allowed"]:
            insights.append(self._make_insight(
                "INS-CYCL-001", "dependency_coupling", "critical",
                "Circular Import Chain", f"Found {len(cycles)} cycles.",
                [c[0] for c in cycles[:3]],
                [TraceabilityRecord("cycles", len(cycles), cfg["cycles_allowed"], "FAIL", "aggregated_metrics.circular_dependencies")],
                "Break cycles via interfaces or lazy imports.",
                self.extractor_id
            ))
        return insights