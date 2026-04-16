# reporting/extractor.py
"""
[Contract: 07-Orchestration / 09-Artifact-Structure]
Unified Architectural Insight Engine.
Merges legacy traceability contracts with modern analytical depth.
Outputs JSON/Markdown/SQL-ready structures for CI/CD Gates & Developer Debugging.
"""
from __future__ import annotations
import time
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# DATA CONTRACTS (Strict Type Safety & JSON Serialization)
# ============================================================================
@dataclass
class TraceabilityRecord:
    """Audit trail linking insight to raw data metrics."""
    metric_name: str
    actual_value: Any
    threshold: Any
    status: str  # PASS | WARN | FAIL
    evidence_path: str

@dataclass
class InsightRecord:
    """Structured insight with multi-metric traceability."""
    insight_id: str
    category: str
    severity: str  # critical | warning | info
    title: str
    description: str
    evidence: List[str]
    traceability_matrix: List[TraceabilityRecord]
    recommendation: str
    layer: str = "global"

# ============================================================================
# CONFIGURABLE THRESHOLDS (Merged Legacy + New)
# ============================================================================
DEFAULT_THRESHOLDS = {
    "cycles_allowed": 0,
    "impact_hotspot": 0.15,          # Legacy: % of codebase affected
    "god_file_impact": 20,           # New: absolute inbound dependencies
    "entropy_warn": 0.6,             # Legacy: structural chaos threshold
    "folder_weight_god": 0.85,       # Merged: overloaded folder score
    "max_depth": 5,                  # New: nesting limit
    "flat_folder_files": 10,         # New: trigger for modularization suggestion
    "unresolved_import_warn": 5,     # Legacy: broken references tolerance
    "orphan_files_allowed": 5,       # New: dead code tolerance
    "health_penalty_critical": 20,   # Legacy CI/CD strictness
    "health_penalty_warning": 10,
    "health_penalty_info": 2
}

# ============================================================================
# INSIGHT EXTRACTOR ENGINE
# ============================================================================
class InsightExtractor:
    """
    Transforms graph_data (nodes/edges/metrics) into auditable, queryable insights.
    Supports multi-format export (JSON/Markdown/SQL) and CI/CD health gating.
    """
    
    def __init__(self, thresholds: Optional[Dict] = None):
        self.thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.counter = 0

    def _next_id(self, category: str) -> str:
        self.counter += 1
        return f"INS-{category.upper()}-{self.counter:03d}"

    def extract(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main orchestration: runs all analysis modules and aggregates results."""
        insights: List[InsightRecord] = []
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        metrics = graph_data.get("aggregated_metrics", {})
        
        # 1. Architectural & Dependency Analysis
        insights.extend(self._analyze_cycles(metrics))
        insights.extend(self._analyze_impact(nodes, edges))
        insights.extend(self._analyze_unresolved_imports(edges))
        
        # 2. Folder & Structural Analysis
        insights.extend(self._analyze_folders(nodes))
        insights.extend(self._analyze_entropy(metrics))
        
        # 3. Scoring & Compilation
        health_score = self._calculate_health_score(insights)
        ranked_lists = self._compile_ranked_lists(nodes, edges)
        recommendations = self._prioritize_actions(insights)

        return {
            "report_version": "1.1.0",
            "metadata": {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "project_root": graph_data.get("metadata", {}).get("root_path", ""),
                "health_score": round(health_score, 1),
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            },
            "insights": [asdict(i) for i in insights],
            "recommendations": recommendations,
            "ranked_lists": ranked_lists,
            "thresholds_applied": self.thresholds
        }

    # ==================== 1. ARCHITECTURAL ANALYSIS ====================
    def _analyze_cycles(self, metrics: Dict) -> List[InsightRecord]:
        insights = []
        cycles = metrics.get("circular_dependencies", [])
        if len(cycles) > self.thresholds["cycles_allowed"]:
            evidence = [c[0] for c in cycles[:5]]
            insights.append(InsightRecord(
                insight_id=self._next_id("CYCLE"),
                category="dependency_coupling",
                severity="critical",
                title="Circular Import Chain Detected",
                description=f"Found {len(cycles)} cycle(s) blocking modular isolation.",
                evidence=evidence,
                traceability_matrix=[
                    TraceabilityRecord("circular_dependencies", len(cycles), self.thresholds["cycles_allowed"], "FAIL", "aggregated_metrics.circular_dependencies")
                ],
                recommendation="Break cycles using interfaces, event buses, or lazy imports."
            ))
        return insights

    def _analyze_impact(self, nodes: List[Dict], edges: List[Dict]) -> List[InsightRecord]:
        insights = []
        # Build inbound dependency map
        inbound: Dict[str, int] = {}
        for e in edges:
            if e.get("relation") == "imports":
                tgt = e.get("target", "")
                inbound[tgt] = inbound.get(tgt, 0) + 1

        total_files = sum(1 for n in nodes if n.get("node_type") == "physical_file")
        hotspots = []
        god_files = []
        
        for n in nodes:
            if n.get("node_type") != "physical_file": continue
            fid = n.get("id", "")
            meta = n.get("physical_meta", {})
            impact_ratio = meta.get("impact_ratio", 0.0)
            dep_count = inbound.get(fid, 0)
            
            if impact_ratio > self.thresholds["impact_hotspot"]:
                hotspots.append(fid)
            if dep_count > self.thresholds["god_file_impact"]:
                god_files.append(fid)

        if hotspots:
            insights.append(InsightRecord(
                insight_id=self._next_id("HOTSPOT"),
                category="impact_concentration",
                severity="warning",
                title="High Blast Radius Files",
                description=f"{len(hotspots)} files affect >{self.thresholds['impact_hotspot']*100:.0f}% of the codebase.",
                evidence=hotspots[:10],
                traceability_matrix=[
                    TraceabilityRecord("high_impact_files", len(hotspots), 0, "WARN", "nodes[*].physical_meta.impact_ratio")
                ],
                recommendation="Isolate core logic, add integration tests, and document change contracts."
            ))
        if god_files:
            insights.append(InsightRecord(
                insight_id=self._next_id("GODFILE"),
                category="centralization_risk",
                severity="critical",
                title="God Files / High Dependency Hubs",
                description=f"{len(god_files)} files are imported by >{self.thresholds['god_file_impact']} modules.",
                evidence=god_files[:10],
                traceability_matrix=[
                    TraceabilityRecord("god_files", len(god_files), 0, "FAIL", "import_dependencies.target_id")
                ],
                recommendation="Apply Facade pattern, split responsibilities, and enforce layer boundaries."
            ))
        return insights

    def _analyze_unresolved_imports(self, edges: List[Dict]) -> List[InsightRecord]:
        insights = []
        unresolved = sum(1 for e in edges if e.get("relation") == "imports" and e.get("confidence") != "EXTRACTED")
        if unresolved > self.thresholds["unresolved_import_warn"]:
            insights.append(InsightRecord(
                insight_id=self._next_id("UNRESOLVED"),
                category="reference_integrity",
                severity="warning",
                title="High Rate of Unresolved Imports",
                description=f"{unresolved} import statements could not be resolved to physical files.",
                evidence=["edge_trace"],
                traceability_matrix=[
                    TraceabilityRecord("unresolved_imports", unresolved, self.thresholds["unresolved_import_warn"], "WARN", "edges[*].confidence")
                ],
                recommendation="Check sys.path configuration, verify virtual environments, or update import regex patterns."
            ))
        return insights

    # ==================== 2. FOLDER & STRUCTURAL ANALYSIS ====================
    def _analyze_folders(self, nodes: List[Dict]) -> List[InsightRecord]:
        insights = []
        folders = [n for n in nodes if n.get("node_type") == "physical_folder"]
        
        for f in folders:
            meta = f.get("physical_meta", {})
            fid = f.get("id", "unknown")
            fname = f.get("label", "unknown")
            depth = meta.get("depth", 0)
            weight = meta.get("weight_score", 0.0)
            file_count = meta.get("file_count", 0)
            sub_count = meta.get("subfolder_count", 0)
            
            # A. Excessive Nesting
            if depth > self.thresholds["max_depth"]:
                insights.append(InsightRecord(
                    insight_id=self._next_id("DEPTH"),
                    category="nesting_complexity",
                    severity="warning",
                    title="Excessive Folder Nesting",
                    description=f"Folder '{fname}' depth ({depth}) exceeds limit ({self.thresholds['max_depth']}).",
                    evidence=[fid],
                    traceability_matrix=[
                        TraceabilityRecord("folder_depth", depth, self.thresholds["max_depth"], "WARN", "nodes[*].physical_meta.depth")
                    ],
                    recommendation="Flatten hierarchy, apply domain-driven folder structure."
                ))
            
            # B. God Folders (Overloaded)
            if weight > self.thresholds["folder_weight_god"]:
                insights.append(InsightRecord(
                    insight_id=self._next_id("GODFOLDER"),
                    category="modular_violation",
                    severity="warning",
                    title="Overloaded Folders (God Folders)",
                    description=f"Folder '{fname}' exceeds structural weight threshold ({weight:.2f}).",
                    evidence=[fid],
                    traceability_matrix=[
                        TraceabilityRecord("folder_weight", round(weight, 3), self.thresholds["folder_weight_god"], "WARN", "nodes[*].physical_meta.weight_score")
                    ],
                    recommendation="Split by domain responsibility. Apply Vertical Slice Architecture."
                ))
                
            # C. Flat Folder Structure
            if sub_count == 0 and file_count > self.thresholds["flat_folder_files"]:
                insights.append(InsightRecord(
                    insight_id=self._next_id("FLAT"),
                    category="structural_organization",
                    severity="info",
                    title="Flat Folder Structure",
                    description=f"Folder '{fname}' contains {file_count} files but no subfolders.",
                    evidence=[fid],
                    traceability_matrix=[
                        TraceabilityRecord("file_count", file_count, self.thresholds["flat_folder_files"], "PASS", "nodes[*].physical_meta.file_count")
                    ],
                    recommendation="Consider grouping related files into feature-specific subdirectories."
                ))
        return insights

    def _analyze_entropy(self, metrics: Dict) -> List[InsightRecord]:
        insights = []
        entropy = metrics.get("global_entropy", 0.0)
        if entropy > self.thresholds["entropy_warn"]:
            insights.append(InsightRecord(
                insight_id=self._next_id("ENTROPY"),
                category="structural_chaos",
                severity="warning",
                title="High Folder Nesting Entropy",
                description=f"Entropy score {entropy:.2f} indicates irregular/deep nesting distribution.",
                evidence=["root_hierarchy"],
                traceability_matrix=[
                    TraceabilityRecord("nesting_entropy", round(entropy, 3), self.thresholds["entropy_warn"], "WARN", "aggregated_metrics.global_entropy")
                ],
                recommendation="Flatten deep directories, apply consistent layering (src/core, src/api)."
            ))
        return insights

    # ==================== 3. SCORING & COMPILATION ====================
    def _calculate_health_score(self, insights: List[InsightRecord]) -> float:
        """CI/CD Gate Formula: Strict penalty scaling."""
        score = 100.0
        for i in insights:
            if i.severity == "critical": score -= self.thresholds["health_penalty_critical"]
            elif i.severity == "warning": score -= self.thresholds["health_penalty_warning"]
            else: score -= self.thresholds["health_penalty_info"]
        return max(0.0, min(100.0, score))

    def _prioritize_actions(self, insights: List[InsightRecord]) -> List[Dict]:
        actions = []
        for i in insights:
            actions.append({
                "priority": 1 if i.severity == "critical" else 2 if i.severity == "warning" else 3,
                "category": i.category,
                "action": i.recommendation,
                "related_insights": [i.insight_id]
            })
        # Deduplicate & sort
        seen = set()
        unique_actions = []
        for a in actions:
            if a["action"] not in seen:
                seen.add(a["action"])
                unique_actions.append(a)
        return sorted(unique_actions, key=lambda x: x["priority"])

    def _compile_ranked_lists(self, nodes: List[Dict], edges: List[Dict]) -> Dict:
        """Provides sortable, BI/SQL-ready lists for queryable insights."""
        folders = [n for n in nodes if n.get("node_type") == "physical_folder"]
        files = [n for n in nodes if n.get("node_type") == "physical_file"]
        
        # Build inbound map for ranking
        inbound: Dict[str, int] = {}
        for e in edges:
            if e.get("relation") == "imports":
                inbound[e.get("target", "")] = inbound.get(e.get("target", ""), 0) + 1

        return {
            "top_heaviest_folders": sorted(folders, key=lambda x: x["physical_meta"].get("weight_score", 0), reverse=True)[:10],
            "deepest_paths": sorted(folders, key=lambda x: x["physical_meta"].get("depth", 0), reverse=True)[:10],
            "most_depended_files": sorted(
                [{"id": f["id"], "name": f["label"], "imported_by": inbound.get(f["id"], 0)} for f in files],
                key=lambda x: x["imported_by"], reverse=True
            )[:10],
            "orphan_files": [f["id"] for f in files if f["id"] not in inbound and f["physical_meta"].get("layer") != "test"][:20]
        }

# ============================================================================
# CLI / MODULE WRAPPER
# ============================================================================
def generate_insights_report(graph_data: Dict[str, Any], output_dir: str | Path = ".", 
                             thresholds: Optional[Dict] = None) -> Dict:
    """Unified entry point for CLI, CI/CD, or programmatic usage."""
    extractor = InsightExtractor(thresholds)
    report = extractor.extract(graph_data)
    
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # 1. JSON Export (Machine-readable, CI/CD Gates)
    (out_path / "architectural_insights.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    
    # 2. Markdown Export (Human-readable, PR Reviews)
    md_content = f"""# 🏗️ Architectural Insights Report
**Health Score:** `{report['metadata']['health_score']}/100` | **Generated:** `{report['metadata']['generated_at']}`

## 📊 Executive Summary
| Metric | Value |
|--------|-------|
| Total Nodes | `{report['metadata']['total_nodes']}` |
| Total Edges | `{report['metadata']['total_edges']}` |
| Critical Issues | `{sum(1 for i in report['insights'] if i['severity']=='critical')}` |
| Warnings | `{sum(1 for i in report['insights'] if i['severity']=='warning')}` |

## 🔍 Top Insights
{chr(10).join(f"- **{i['title']}** ({i['severity'].upper()}): {i['description']}" for i in report['insights'][:5])}

## 📈 Ranked Architectural Views
- **Heaviest Folders:** {', '.join(f['label'] for f in report['ranked_lists']['top_heaviest_folders'][:3])}
- **Most Depended Files:** {', '.join(f['name'] for f in report['ranked_lists']['most_depended_files'][:3])}

---
*Generated by Graphify Physical Analyzer v1.1.0*
"""
    (out_path / "architectural_insights.md").write_text(md_content, encoding="utf-8")
    
    logger.info("✅ Insights report generated: JSON & Markdown")
    return report

__all__ = ["InsightExtractor", "DEFAULT_THRESHOLDS", "generate_insights_report"]