# reporting/aggregators/aggregator.py
"""
[Contract: 07-Orchestration] Unified Report Aggregator.
Manages extractor registry, executes config-driven pipeline, computes normalized health,
and outputs Graphify-compatible report structure.
"""
from __future__ import annotations
import time
import logging
from typing import Dict, List, Any, Optional

from ports.insight import IReportAggregator, IInsightExtractor, InsightRecord

logger = logging.getLogger(__name__)

DEFAULT_AGG_CONFIG = {
    "active_extractors": ["structure", "dependency", "impact"],
    "threshold_overrides": {},
    "health_penalties": {"critical": 3.0, "warning": 1.0, "info": 0.1},
    "raw_findings_mode": False
}

class InsightAggregator(IReportAggregator):
    """Config-driven orchestrator implementing IReportAggregator."""
    
    def __init__(self):
        self._registry: Dict[str, IInsightExtractor] = {}

    def register_extractor(self, extractor: IInsightExtractor) -> None:
        self._registry[extractor.extractor_id] = extractor

    def execute(self, raw_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = {**DEFAULT_AGG_CONFIG, **(config or {})}
        active_ids = [eid for eid in cfg["active_extractors"] if eid in self._registry]
        
        all_insights: List[InsightRecord] = []
        raw_findings: Dict[str, Any] = {}
        overrides = cfg.get("threshold_overrides", {})

        for eid in active_ids:
            ext = self._registry[eid]
            thr = {**ext.default_thresholds, **overrides.get(eid, {})}
            
            if cfg.get("raw_findings_mode"):
                raw_findings[eid] = ext.get_raw_findings(raw_data)
            
            all_insights.extend(ext.extract(raw_data, thr))

        total_nodes = len(raw_data.get("nodes", []))
        health = self.calculate_health(all_insights, total_nodes, cfg["health_penalties"])
        
        # Safe serialization for dataclasses
        serialized_insights = []
        for i in all_insights:
            d = i.__dict__.copy()
            d["traceability_matrix"] = [t.__dict__ for t in i.traceability_matrix]
            serialized_insights.append(d)

        return {
            "report_version": "2.0-unified",
            "metadata": {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "project_root": raw_data.get("metadata", {}).get("root_path", ""),
                "health_score": health,
                "total_nodes": total_nodes,
                "total_edges": len(raw_data.get("edges", [])),
                "active_extractors": active_ids
            },
            "insights": serialized_insights,
            "raw_findings": raw_findings,
            "thresholds_applied": overrides
        }

    def calculate_health(self, insights: List[InsightRecord], total_nodes: int, penalties: Dict[str, float]) -> float:
        if not insights: return 100.0
        crit = sum(1 for i in insights if i.severity == "critical")
        warn = sum(1 for i in insights if i.severity == "warning")
        info = sum(1 for i in insights if i.severity == "info")
        
        weighted = (crit * penalties["critical"]) + (warn * penalties["warning"]) + (info * penalties["info"])
        size_factor = max(1.0, total_nodes / 1000.0)
        deduction = min(70.0, (weighted / size_factor) * 10.0)
        return round(max(30.0, 100.0 - deduction), 1)

__all__ = ["InsightAggregator", "DEFAULT_AGG_CONFIG"]