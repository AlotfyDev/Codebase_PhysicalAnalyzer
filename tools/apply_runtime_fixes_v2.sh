#!/usr/bin/env bash
set -euo pipefail

BRANCH_NAME="${1:-fix/runtime-gaps-and-prune-obsolete}"
COMMIT_MSG="fix: apply runtime corrections and prune obsolete artifacts"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must be run inside a git repository." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "$BRANCH_NAME" ]]; then
  git checkout -B "$BRANCH_NAME"
fi

rm -f application/run_analysis_Obsolete.py \
      reporting/generator_obsolete.py \
      reporting/aggregators/aggregator_obsolete.py \
      reporting/extractors/dependency_obsolete.py \
      reporting/extractors/base_obsolete.py \
      adapters/import_/base_obsolete.py \
      adapters/export/base_obsolete.py

python3 <<'PY'
from pathlib import Path

files = {
    "application/orchestrator.py": '''# application/orchestrator.py
"""
Application Layer Orchestrator: [Contract: 07-orchestration, 04-abstraction, 08-IO]
Binds domain stages sequentially, manages shared AnalysisContext, handles Fail-Soft/Fail-Fast errors,
and exposes a high-level run_analysis() API compatible with Graphify's extraction pipeline.
"""
from __future__ import annotations
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain.types import AnalysisContext, StageResult
from domain.scanner import ScannerStage
from domain.metrics import MetricsStage
from domain.classifier import ClassifierStage
from domain.import_extractor import ImportExtractorStage
from domain.graph_builder import GraphBuilderStage

# Safe import for config adapter (provides fallback during early refactoring)
try:
    from adapters.config.json_ignored import JsonConfigLoader

    _cfg_loader = JsonConfigLoader()

    def load_ignore_patterns(root: Path) -> List[str]:
        return _cfg_loader.load_ignore_patterns(root)

    def load_config(root: Path) -> Dict[str, Any]:
        return _cfg_loader.load_config(root)
except ImportError:
    def load_ignore_patterns(root: Path) -> List[str]:
        return []

    def load_config(root: Path) -> Dict[str, Any]:
        return {
            "layer_rules": {},
            "weight_coeffs": {"density": 0.5, "depth_penalty": 0.3, "centrality": 0.2},
            "max_file_size_mb": 5,
        }


class PhysicalAnalyzerOrchestrator:
    """
    [Contract: 07-BehavioralOrchestration]
    Central coordinator for the Physical Analyzer pipeline.
    Executes stages in strict order, propagates context, aggregates diagnostics,
    and guarantees deterministic output or controlled failure.
    """

    def __init__(self, root_path: Path, config_overrides: Optional[Dict] = None):
        self.root_path = root_path.resolve()
        self.config_overrides = config_overrides or {}
        self._stages = [
            ScannerStage(),
            MetricsStage(),
            ClassifierStage(),
            ImportExtractorStage(),
            GraphBuilderStage(),
        ]

    def execute(self) -> StageResult:
        """
        [Contract: 04-IPhysicalPipeline]
        Main execution loop. Manages context flow, error aggregation, and stage gating.
        """
        ignore_patterns = load_ignore_patterns(self.root_path)
        cfg = load_config(self.root_path)

        if "layer_rules" in self.config_overrides:
            cfg.setdefault("layer_rules", {}).update(self.config_overrides["layer_rules"])
        if "weight_coeffs" in self.config_overrides:
            cfg.setdefault("weight_coeffs", {}).update(self.config_overrides["weight_coeffs"])
        if "max_file_size_mb" in self.config_overrides:
            cfg["max_file_size_mb"] = self.config_overrides["max_file_size_mb"]

        ctx = AnalysisContext(
            root_path=self.root_path,
            ignore_patterns=ignore_patterns,
            layer_rules=cfg.get("layer_rules", {}),
            weight_coeffs=cfg.get("weight_coeffs", {}),
            max_file_size_mb=cfg.get("max_file_size_mb", 5),
        )
        ctx.data["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"

        all_errors: List[str] = []
        all_warnings: List[str] = []

        for stage in self._stages:
            try:
                res = stage.execute(ctx)
                for err in ctx.parse_errors:
                    all_errors.append(err.get("error", str(err)))
                ctx.parse_errors.clear()
                all_errors.extend(res.errors)
                all_warnings.extend(res.warnings)

                if not res.success:
                    all_errors.append(f"[FAIL-FAST] Stage '{stage.stage_id}' returned success=False")
                    return StageResult(success=False, data={}, errors=list(dict.fromkeys(all_errors)))

            except Exception as exc:
                all_errors.append(f"[UNHANDLED] Exception in '{stage.stage_id}': {exc}")
                return StageResult(success=False, data={}, errors=list(dict.fromkeys(all_errors)))

        final_data = ctx.data
        return StageResult(
            success=True,
            data=final_data,
            errors=list(dict.fromkeys(all_errors)),
            warnings=list(dict.fromkeys(all_warnings)),
        )


def run_analysis(root_path: str, config_overrides: Optional[Dict] = None) -> Dict[str, Any]:
    """
    [Contract: 08-IO-HighLevelAPI]
    Synchronous, high-level entry point for direct module/CLI integration.
    Returns Graphify-compatible extraction_dict or raises RuntimeError on failure.
    """
    orchestrator = PhysicalAnalyzerOrchestrator(Path(root_path), config_overrides)
    result = orchestrator.execute()

    if not result.success:
        raise RuntimeError(f"Physical analysis failed: {' | '.join(result.errors)}")
    return result.data


__all__ = ["PhysicalAnalyzerOrchestrator", "run_analysis"]
''',
    "reporting/aggregators/aggregator.py": '''# reporting/aggregators/aggregator.py
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
    "raw_findings_mode": False,
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
                "active_extractors": active_ids,
            },
            "insights": serialized_insights,
            "raw_findings": raw_findings,
            "thresholds_applied": overrides,
        }

    def calculate_health(self, insights: List[InsightRecord], total_nodes: int, penalties: Dict[str, float]) -> float:
        if not insights:
            return 100.0
        crit = sum(1 for i in insights if i.severity == "critical")
        warn = sum(1 for i in insights if i.severity == "warning")
        info = sum(1 for i in insights if i.severity == "info")

        weighted = (crit * penalties["critical"]) + (warn * penalties["warning"]) + (info * penalties["info"])
        size_factor = max(1.0, total_nodes / 1000.0)
        deduction = min(70.0, (weighted / size_factor) * 10.0)
        return round(max(30.0, 100.0 - deduction), 1)

__all__ = ["InsightAggregator", "DEFAULT_AGG_CONFIG"]
''',
    "reporting/extractors/structure.py": '''# reporting/extractors/structure.py
"""Extractor for folder depth, weight, entropy, and structural organization."""
from __future__ import annotations
from typing import Dict, List, Any
from .base import IInsightExtractor, InsightRecord, TraceabilityRecord

class StructureExtractor(IInsightExtractor):
    @property
    def extractor_id(self) -> str:
        return "structure"

    @property
    def default_thresholds(self) -> Dict[str, Any]:
        return {"max_depth": 5, "folder_weight_god": 0.85, "entropy_warn": 0.6, "flat_folder_files": 10}

    def get_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        folders = [n for n in raw_data.get("nodes", []) if n.get("node_type") == "physical_folder"]
        return {
            "folder_tree_depths": {f["id"]: f["physical_meta"].get("depth", 0) for f in folders},
            "folder_weights": {f["id"]: f["physical_meta"].get("weight_score", 0.0) for f in folders},
            "global_entropy": raw_data.get("aggregated_metrics", {}).get("global_entropy", 0.0),
        }

    def extract(self, raw_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]:
        insights = []
        cfg = {**self.default_thresholds, **thresholds}
        folders = [n for n in raw_data.get("nodes", []) if n.get("node_type") == "physical_folder"]

        for f in folders:
            meta = f.get("physical_meta", {})
            fid, fname = f.get("id", "unknown"), f.get("label", "unknown")
            depth = meta.get("depth", 0)
            weight = meta.get("weight_score", 0.0)
            fc = meta.get("file_count", 0)
            sc = meta.get("subfolder_count", 0)

            if depth > cfg["max_depth"]:
                insights.append(InsightRecord(
                    f"INS-DEPTH-{len(insights)+1:03d}", "nesting_complexity", "warning",
                    "Excessive Folder Nesting", f"'{fname}' depth ({depth}) > limit ({cfg['max_depth']}).",
                    [fid], [TraceabilityRecord("folder_depth", depth, cfg["max_depth"], "WARN", "nodes[*].physical_meta.depth")],
                    "Flatten hierarchy or apply domain-driven structure.", self.extractor_id,
                ))
            if weight > cfg["folder_weight_god"]:
                insights.append(InsightRecord(
                    f"INS-GODF-{len(insights)+1:03d}", "modular_violation", "warning",
                    "Overloaded Folder (God Folder)", f"'{fname}' weight ({weight:.2f}) > threshold.",
                    [fid], [TraceabilityRecord("folder_weight", round(weight, 3), cfg["folder_weight_god"], "WARN", "nodes[*].physical_meta.weight_score")],
                    "Split by domain responsibility. Apply Vertical Slices.", self.extractor_id,
                ))
            if sc == 0 and fc > cfg["flat_folder_files"]:
                insights.append(InsightRecord(
                    f"INS-FLAT-{len(insights)+1:03d}", "structural_organization", "info",
                    "Flat Folder Structure", f"'{fname}' has {fc} files, 0 subfolders.",
                    [fid], [TraceabilityRecord("file_count", fc, cfg["flat_folder_files"], "PASS", "nodes[*].physical_meta.file_count")],
                    "Group related files into feature subdirectories.", self.extractor_id,
                ))

        entropy = raw_data.get("aggregated_metrics", {}).get("global_entropy", 0.0)
        if entropy > cfg["entropy_warn"]:
            insights.append(InsightRecord(
                f"INS-ENTR-{len(insights)+1:03d}", "structural_chaos", "warning",
                "High Nesting Entropy", f"Entropy {entropy:.2f} indicates irregular distribution.",
                ["root_hierarchy"], [TraceabilityRecord("nesting_entropy", round(entropy, 3), cfg["entropy_warn"], "WARN", "aggregated_metrics.global_entropy")],
                "Standardize layering (src/core, src/api, src/utils).", self.extractor_id,
            ))
        return insights
''',
    "reporting/extractors/impact.py": '''# reporting/extractors/impact.py
"""Extractor for impact hotspots, god files, and orphaned modules."""
from __future__ import annotations
from typing import Dict, List, Any
from .base import IInsightExtractor, InsightRecord, TraceabilityRecord

class ImpactExtractor(IInsightExtractor):
    @property
    def extractor_id(self) -> str:
        return "impact"

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

        inbound: Dict[str, int] = {}
        for e in edges:
            if e.get("relation") == "imports":
                inbound[e.get("target", "")] = inbound.get(e.get("target", ""), 0) + 1

        hotspots, god_files, orphans = [], [], []
        for n in nodes:
            if n.get("node_type") != "physical_file":
                continue
            fid, meta = n.get("id", ""), n.get("physical_meta", {})
            impact_ratio = meta.get("impact_ratio", 0.0)
            dep_count = inbound.get(fid, 0)
            layer = meta.get("layer", "")

            if impact_ratio > cfg["impact_hotspot"]:
                hotspots.append(fid)
            if dep_count > cfg["god_file_impact"]:
                god_files.append(fid)
            if dep_count == 0 and layer != "test":
                orphans.append(fid)

        if hotspots:
            insights.append(InsightRecord(
                "INS-HOTS-001", "impact_concentration", "warning",
                "High Blast Radius Files", f"{len(hotspots)} files affect >{cfg['impact_hotspot']*100:.0f}% of codebase.",
                hotspots[:10], [TraceabilityRecord("high_impact_files", len(hotspots), 0, "WARN", "nodes[*].physical_meta.impact_ratio")],
                "Isolate core logic, add integration tests, document change contracts.", self.extractor_id,
            ))
        if god_files:
            insights.append(InsightRecord(
                "INS-GODF-001", "centralization_risk", "critical",
                "God Files / Dependency Hubs", f"{len(god_files)} files imported by >{cfg['god_file_impact']} modules.",
                god_files[:10], [TraceabilityRecord("god_files", len(god_files), 0, "FAIL", "import_dependencies.target_id")],
                "Apply Facade pattern, split responsibilities, enforce layer boundaries.", self.extractor_id,
            ))
        if len(orphans) > cfg["orphan_files_allowed"]:
            insights.append(InsightRecord(
                "INS-ORPH-001", "dead_code_risk", "info",
                "Orphan Files Detected", f"{len(orphans)} files have 0 inbound imports.",
                orphans[:10], [TraceabilityRecord("orphan_count", len(orphans), cfg["orphan_files_allowed"], "PASS", "nodes[*].id")],
                "Review for deletion or archival.", self.extractor_id,
            ))
        return insights
''',
    "adapters/graphify/pipeline_hook.py": '''# adapters/graphify/pipeline_hook.py
"""
Pipeline Hook: Integrates Physical Analyzer into Graphify's extraction/build flow.
Fail-Soft by design: logs diagnostics, merges results, never breaks main pipeline.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from application.api import run_analysis_safe
from application.safe_merger import safe_merge

logger = logging.getLogger(__name__)


def inject_physical_analysis(
    root_path: str,
    args: Any,
    existing_extractions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    [Contract: 04-IPipelineHook]
    Executes physical analysis if enabled, merges nodes/edges/metadata into
    Graphify's extraction_dict, and prepares data for downstream export/reporting.
    """
    if not getattr(args, "codebase_report", False):
        return existing_extractions or {"nodes": [], "edges": [], "metadata": {}}

    logger.info("🔍 Starting Physical Codebase Analysis...")
    output_dir = Path(getattr(args, "output", "graphify-out"))
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_analysis_safe(root_path, config_overrides=None)

    if not result["success"]:
        logger.warning("⚠️ Physical analysis completed with diagnostics: %s", result["errors"])
    else:
        physical_data = result["data"]
        logger.info(
            "✅ Analysis complete: %d nodes, %d edges, %d entry points, %d cycles",
            len(physical_data.get("nodes", [])),
            len(physical_data.get("edges", [])),
            len(physical_data.get("aggregated_metrics", {}).get("entry_point_candidates", [])),
            len(physical_data.get("aggregated_metrics", {}).get("circular_dependencies", [])),
        )

    merged = existing_extractions or {"nodes": [], "edges": [], "metadata": {}}
    physical_data = result["data"]

    merge_result = safe_merge(physical_data, merged)
    merged = merge_result.merged_dict
    merged["metadata"]["physical_analysis"] = physical_data.get("metadata", {})
    merged["metadata"]["physical_report"] = {
        "success": result["success"],
        "errors": result["errors"],
        "warnings": result["warnings"],
        "generated_at": physical_data.get("metadata", {}).get("timestamp", ""),
    }

    _schedule_routing(result, args, output_dir)
    return merged


def _schedule_routing(result: Dict[str, Any], args: Any, output_dir: Path) -> None:
    """
    Internal dispatcher. Prepares context for future Report Generator & Relational Bridge.
    Keeps pipeline hook clean while preserving extension points.
    """
    pass


__all__ = ["inject_physical_analysis"]
''',
}

for path_str, content in files.items():
    path = Path(path_str)
    path.write_text(content, encoding="utf-8")
PY

python3 -m compileall application adapters reporting domain infrastructure ports >/dev/null

git add application/orchestrator.py \
        reporting/aggregators/aggregator.py \
        reporting/extractors/structure.py \
        reporting/extractors/impact.py \
        adapters/graphify/pipeline_hook.py \
        tools/apply_runtime_fixes_v2.sh

git add -u

if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

git commit -m "$COMMIT_MSG"
git push -u origin "$BRANCH_NAME"

echo
echo "Done. Branch pushed: $BRANCH_NAME"
