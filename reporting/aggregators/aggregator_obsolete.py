# reporting/aggregator.py
"""
[Contract: 07-Orchestration] Insight Aggregator & Report Composer.
Runs extractors independently or combined, applies config, calculates health score,
and outputs unified report compatible with generator.py & CI/CD gates.
"""
from __future__ import annotations
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal

from .extractors.base import IInsightExtractor, InsightRecord, asdict
from .extractors.structure import StructureExtractor
from .extractors.dependency import DependencyExtractor
from .extractors.impact import ImpactExtractor

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "mode": "combined",  # "combined" | "independent"
    "extractors": ["structure", "dependency", "impact"],
    "thresholds": {},
    "health_penalty": {"critical": 3.0, "warning": 1.0, "info": 0.1}
}

class InsightAggregator:
    def __init__(self, config: Optional[Dict] = None):
        self.cfg = {**DEFAULT_CONFIG, **(config or {})}
        self.registry: Dict[str, IInsightExtractor] = {
            "structure": StructureExtractor(),
            "dependency": DependencyExtractor(),
            "impact": ImpactExtractor()
        }

    def run(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution: filters extractors, runs them, aggregates results."""
        selected_ids = [eid for eid in self.cfg["extractors"] if eid in self.registry]
        all_insights: List[InsightRecord] = []
        raw_findings: Dict[str, Any] = {}

        for eid in selected_ids:
            ext = self.registry[eid]
            thr = {**ext.default_thresholds, **self.cfg["thresholds"].get(eid, {})}
            
            # Collect raw material first (for BI/SQL querying)
            raw_findings[eid] = ext.collect_raw_findings(raw_data)
            # Generate insights with thresholds
            all_insights.extend(ext.extract(raw_data, thr))

        health = self._calculate_health(all_insights, len(raw_data.get("nodes", [])))
        ranked = self._compile_ranked(raw_data, all_insights)
        recs = self._prioritize_recommendations(all_insights)

        report = {
            "report_version": "2.0.0-modular",
            "metadata": {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "project_root": raw_data.get("metadata", {}).get("root_path", ""),
                "health_score": health,
                "total_nodes": len(raw_data.get("nodes", [])),
                "total_edges": len(raw_data.get("edges", [])),
                "extractors_run": selected_ids,
                "mode": self.cfg["mode"]
            },
            "insights": [asdict(i) for i in all_insights],
            "recommendations": recs,
            "ranked_lists": ranked,
            "raw_findings": raw_findings if self.cfg["mode"] == "independent" else {},
            "thresholds_applied": self.cfg["thresholds"]
        }
        return report

    def _calculate_health(self, insights: List[InsightRecord], total_nodes: int) -> float:
        if not insights: return 100.0
        weights = self.cfg["health_penalty"]
        crit = sum(1 for i in insights if i.severity == "critical")
        warn = sum(1 for i in insights if i.severity == "warning")
        info = sum(1 for i in insights if i.severity == "info")
        
        weighted = (crit * weights["critical"]) + (warn * weights["warning"]) + (info * weights["info"])
        size_factor = max(1.0, total_nodes / 1000.0)
        deduction = min(70.0, (weighted / size_factor) * 10.0)
        return round(max(30.0, 100.0 - deduction), 1)

    def _compile_ranked(self, raw_data: Dict, insights: List[InsightRecord]) -> Dict:
        nodes = raw_data.get("nodes", [])
        folders = [n for n in nodes if n.get("node_type") == "physical_folder"]
        files = [n for n in nodes if n.get("node_type") == "physical_file"]
        return {
            "top_heaviest_folders": sorted(folders, key=lambda x: x["physical_meta"].get("weight_score", 0), reverse=True)[:10],
            "deepest_paths": sorted(folders, key=lambda x: x["physical_meta"].get("depth", 0), reverse=True)[:10],
            "flagged_by_insights": list({i.insight_id: i.category for i in insights}.items())[:20]
        }

    def _prioritize_recommendations(self, insights: List[InsightRecord]) -> List[Dict]:
        seen = set()
        recs = []
        for i in insights:
            if i.recommendation not in seen:
                seen.add(i.recommendation)
                recs.append({"priority": 1 if i.severity=="critical" else 2 if i.severity=="warning" else 3, "action": i.recommendation})
        return sorted(recs, key=lambda x: x["priority"])

def generate_report(raw_ Dict, output_dir: str | Path = ".", config: Optional[Dict] = None) -> Dict:
    agg = InsightAggregator(config)
    report = agg.run(raw_data)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "architectural_report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    logger.info("✅ Modular report generated: %s mode", report["metadata"]["mode"])
    return report

__all__ = ["InsightAggregator", "generate_report", "DEFAULT_CONFIG"]