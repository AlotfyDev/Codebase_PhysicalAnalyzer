# application/runner.py
"""
[Contract: 07-Orchestration / 08-IO]
Unified System Runner & CLI Entry Point.
Orchestrates: Analysis Pipeline → Insight Aggregation → Report Generation.
Handles config, extractor registration, health scoring, and CI/CD exit codes.
"""
from __future__ import annotations
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from application.api import run_analysis
from reporting.aggregators.aggregator import InsightAggregator, DEFAULT_AGG_CONFIG
from reporting.extractors.structure import StructureExtractor
from reporting.extractors.dependency import DependencyExtractor
from reporting.extractors.impact import ImpactExtractor
from reporting.generator import generate_dynamic_report

logger = logging.getLogger(__name__)

class PhysicalAnalyzerRunner:
    """
    [Contract: High-Level Orchestrator]
    Binds domain pipeline, modular extractors, and reporting into a single execution flow.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agg = InsightAggregator()
        self._register_defaults()

    def _register_defaults(self):
        """Auto-register core extractors. Extensible via config later."""
        for ext in [StructureExtractor(), DependencyExtractor(), ImpactExtractor()]:
            self.agg.register_extractor(ext)

    def run(self, root_path: str, output_dir: str = ".", config_overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """End-to-end execution: Scan → Aggregate → Report."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # 1. Run Core Pipeline
        logger.info("🔍 Starting Physical Analysis Pipeline...")
        graph_data = run_analysis(root_path, config_overrides)

        # 2. Merge Aggregator Config
        agg_cfg = {**DEFAULT_AGG_CONFIG, **self.config.get("aggregator", {})}
        if config_overrides and "thresholds" in config_overrides:
            agg_cfg["threshold_overrides"] = config_overrides["thresholds"]

        # 3. Run Insight Aggregation
        logger.info("📊 Generating Architectural Insights...")
        report = self.agg.execute(graph_data, config=agg_cfg)

        # 4. Generate Human-Readable Report
        if self.config.get("generate_markdown", True):
            generate_dynamic_report(report, output_dir=out_path, filename="architectural_report.md")
            logger.info("📄 Markdown report saved to %s", out_path / "architectural_report.md")

        # 5. Save Raw JSON (for BI/SQL/CI-CD/Graphify)
        (out_path / "architectural_report.json").write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8"
        )
        logger.info("💾 Raw JSON report saved to %s", out_path / "architectural_report.json")

        logger.info("✅ Runner completed. Health: %s | Insights: %d", 
                    report["metadata"]["health_score"], len(report["insights"]))
        return report


def main(root_path: str = ".", output_dir: str = ".", config: Optional[Dict] = None) -> int:
    """
    [Contract: CLI/Module Entry Point]
    Returns exit code for CI/CD gates:
      0 = Healthy (>=80)
      1 = Warnings (60-79)
      2 = Critical (<60)
      3 = Runtime Error
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        runner = PhysicalAnalyzerRunner(config)
        report = runner.run(root_path, output_dir, config)
        score = report["metadata"]["health_score"]
        
        if score >= 80: return 0
        elif score >= 60: return 1
        else: return 2
    except Exception as e:
        logger.error("❌ Runner failed: %s", e, exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())