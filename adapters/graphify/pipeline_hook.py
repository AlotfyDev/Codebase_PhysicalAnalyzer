# adapters/graphify/pipeline_hook.py
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
    existing_extractions: Optional[Dict[str, Any]] = None
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

    # Execute analysis (safe variant guarantees structured output even on partial failure)
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
            len(physical_data.get("aggregated_metrics", {}).get("circular_dependencies", []))
        )

    # Merge into Graphify extraction_dict using safe_merge
    merged = existing_extractions or {"nodes": [], "edges": [], "metadata": {}}
    physical_data = result["data"]

    # Use safe_merge to prevent duplicate nodes/edges and enrich existing nodes
    merge_result = safe_merge(physical_data, merged)
    merged = merge_result.merged_dict

    # Add physical analysis metadata
    merged["metadata"]["physical_analysis"] = physical_data.get("metadata", {})
    merged["metadata"]["physical_report"] = {
        "success": result["success"],
        "errors": result["errors"],
        "warnings": result["warnings"],
        "generated_at": physical_data.get("metadata", {}).get("timestamp", ""),
        "merge_stats": merge_result.stats
    }

    # Dispatcher placeholder: will wire to reporting/ & relational_bridge/ in next iteration
    _schedule_routing(result, args, output_dir)

    return merged


def _schedule_routing(result: Dict[str, Any], args: Any, output_dir: Path) -> None:
    """
    Internal dispatcher. Prepares context for future Report Generator & Relational Bridge.
    Keeps pipeline hook clean while preserving extension points.
    """
    # Future: 
    # if args.report_format: reporting/generator.py.render(...)
    # if args.relational_export: application/relational_bridge.py.forward(...)
    pass


__all__ = ["inject_physical_analysis"]