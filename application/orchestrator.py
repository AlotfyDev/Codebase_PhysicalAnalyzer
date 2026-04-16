# application/orchestrator.py
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
    from adapters.config.json_ignored import load_config, load_ignore_patterns
except ImportError:
    def load_ignore_patterns(root: Path) -> List[str]: return []
    def load_config(root: Path) -> Dict[str, Any]:
        return {
            "layer_rules": {},
            "weight_coeffs": {"density": 0.5, "depth_penalty": 0.3, "centrality": 0.2},
            "max_file_size_mb": 5
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
            GraphBuilderStage()
        ]

    def execute(self) -> StageResult:
        """
        [Contract: 04-IPhysicalPipeline]
        Main execution loop. Manages context flow, error aggregation, and stage gating.
        """
        # 1. Load Configuration & Initialize Context
        ignore_patterns = load_ignore_patterns(self.root_path)
        cfg = load_config(self.root_path)
        
        # Apply runtime overrides
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
            max_file_size_mb=cfg.get("max_file_size_mb", 5)
        )
        ctx.data["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"

        all_errors: List[str] = []
        all_warnings: List[str] = []

        # 2. Sequential Stage Execution
        for stage in self._stages:
            try:
                res = stage.execute(ctx)
                
                # Aggregate diagnostics (Fail-Soft tracking)
                for err in ctx.parse_errors:
                    all_errors.append(err.get("error", str(err)))
                ctx.parse_errors.clear()  # Prevent duplication across stages
                all_errors.extend(res.errors)
                all_warnings.extend(res.warnings)

                # Fail-Fast gate: Stop pipeline on critical stage failure
                if not res.success:
                    all_errors.append(f"[FAIL-FAST] Stage '{stage.stage_id}' returned success=False")
                    return StageResult(success=False, data={}, errors=list(dict.fromkeys(all_errors)))

            except Exception as exc:
                all_errors.append(f"[UNHANDLED] Exception in '{stage.stage_id}': {exc}")
                return StageResult(success=False, data={}, errors=list(dict.fromkeys(all_errors)))

        # 3. Success Path & Deduplication
        final_data = ctx.data  # Contains nodes, edges, metadata, aggregated_metrics
        return StageResult(
            success=True,
            data=final_data,
            errors=list(dict.fromkeys(all_errors)),
            warnings=list(dict.fromkeys(all_warnings))
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
__all__ = ["PhysicalAnalyzerOrchestrator", "run_analysis"]