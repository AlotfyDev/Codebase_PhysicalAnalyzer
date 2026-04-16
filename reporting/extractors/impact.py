# reporting/extractors/impact.py
"""Extractor for impact hotspots, god files, and orphaned modules."""
from __future__ import annotations
from typing import Dict, List, Any
from .base import IInsightExtractor, InsightRecord, TraceabilityRecord

class ImpactExtractor(IInsightExtractor):
    @property
    def extractor_id(self) -> str: return "impact"
    @property
    def default_thresholds(self) -> Dict[str, Any]:
        return {"impact_hotspot": 0.15, "god_file_impact": 20, "orphan_files_allowed": 5}

    def get_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        edges = raw_data.get("edges", [])
        inbound: Dict[str, int] = {}
        for e in edges:
            if e.get("relation") == "imports":
                inbound[e.get("target", "")] = inbound.get(e.get("target", ""), 0) + 1
        return {"inbound_dependency_map": inbound}

    def extract(self, raw_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]:
        insights = []
        cfg = {**self.default_thresholds, **thresholds}
        nodes = raw_data.get("nodes", [])
        edges = raw_data.get("edges", [])
        total_files = sum(1 for n in nodes if n.get("node_type") == "physical_file")

        inbound: Dict[str, int] = {}
        for e in edges:
            if e.get("relation") == "imports":
                inbound[e.get("target", "")] = inbound.get(e.get("target", ""), 0) + 1

        hotspots, god_files, orphans = [], [], []
        for n in nodes:
            if n.get("node_type") != "physical_file": continue
            fid, meta = n.get("id", ""), n.get("physical_meta", {})
            impact_ratio = meta.get("impact_ratio", 0.0)
            dep_count = inbound.get(fid, 0)
            layer = meta.get("layer", "")
            
            if impact_ratio > cfg["impact_hotspot"]: hotspots.append(fid)
            if dep_count > cfg["god_file_impact"]: god_files.append(fid)
            if dep_count == 0 and layer != "test": orphans.append(fid)

        if hotspots:
            insights.append(InsightRecord("INS-HOTS-001", "impact_concentration", "warning",
                "High Blast Radius Files", f"{len(hotspots)} files affect >{cfg['impact_hotspot']*100:.0f}% of codebase.",
                hotspots[:10], [TraceabilityRecord("high_impact_files", len(hotspots), 0, "WARN", "nodes[*].physical_meta.impact_ratio")],
                "Isolate core logic, add integration tests, document change contracts.", self.extractor_id))
        if god_files:
            insights.append(InsightRecord("INS-GODF-001", "centralization_risk", "critical",
                "God Files / Dependency Hubs", f"{len(god_files)} files imported by >{cfg['god_file_impact']} modules.",
                god_files[:10], [TraceabilityRecord("god_files", len(god_files), 0, "FAIL", "import_dependencies.target_id")],
                "Apply Facade pattern, split responsibilities, enforce layer boundaries.", self.extractor_id))
        if len(orphans) > cfg["orphan_files_allowed"]:
            insights.append(InsightRecord("INS-ORPH-001", "dead_code_risk", "info",
                "Orphan Files Detected", f"{len(orphans)} files have 0 inbound imports.",
                orphans[:10], [TraceabilityRecord("orphan_count", len(orphans), cfg["orphan_files_allowed"], "PASS", "nodes[*].id")],
                "Review for deletion or archival.", self.extractor_id))
        return insights