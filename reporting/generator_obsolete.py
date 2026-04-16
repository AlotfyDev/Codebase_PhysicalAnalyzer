# reporting/generator.py
"""
[Contract: 04-Abstraction] Implements ports.report.IReportGenerator.
Wraps legacy Jinja2 logic in a protocol-compliant, registry-ready strategy.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Template

from ports.report import IReportGenerator, RenderReport
from reporting.generator import generate_dynamic_report
generate_dynamic_report(report, output_dir="./reports", filename="architecture.md")
MARKDOWN_TEMPLATE = """... (نفس القالب القديم تمامًا) ..."""

class MarkdownReportGenerator(IReportGenerator):
    @property
    def format_name(self) -> str:
        return "markdown"

    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.template = Template(MARKDOWN_TEMPLATE)
        self._register_filters()

    def _register_filters(self):
        self.template.environment.filters["status_badge"] = lambda s: {
            "PASS": "🟢", "WARN": "🟡", "FAIL": "🔴", "INFO": "🔵"
        }.get(str(s).upper(), f"⚪ {s}")
        
        self.template.environment.filters["health_badge"] = lambda sc: (
            f"🟢 Excellent ({sc:.0f})" if sc >= 90 else
            f"🟡 Good ({sc:.0f})" if sc >= 70 else
            f"🟠 Needs Work ({sc:.0f})" if sc >= 50 else
            f"🔴 Critical ({sc:.0f})"
        )
        self.template.environment.filters["basename"] = lambda p: Path(p).name if p else "N/A"

    # ✅ FIX 1: Added missing colon in type hint
    def _build_context(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        insights = report_data.get("insights", [])
        metrics = report_data.get("metadata", {})
        return {
            "metadata": metrics,
            "summary_metrics": [
                {"name": "Health Score", "value": metrics.get("health_score", "N/A"), "status": "INFO"},
                {"name": "Critical", "value": sum(1 for i in insights if i.get("severity") == "critical"),
                 "status": "FAIL" if any(i.get("severity") == "critical" for i in insights) else "PASS"},
            ],
            "critical_insights": [i for i in insights if i.get("severity") == "critical"],
            "warning_insights": [i for i in insights if i.get("severity") == "warning"],
            "info_insights": [i for i in insights if i.get("severity") == "info"],
            "all_insights": insights,
            "recommendations": report_data.get("recommendations", []),
            "version": self.version
        }

    # ✅ FIX 2: Added missing colon in type hint
    def render(self, report_data: Dict[str, Any], output_dir: Path, filename: Optional[str] = None, **kwargs) -> RenderReport:
        context = self._build_context(report_data)
        content = self.template.render(**context)
        out_path = output_dir / (filename or f"architectural_report.{self.format_name}")
        out_path.write_text(content, encoding="utf-8")
        return RenderReport(success=True, content=content, output_path=out_path, format_name=self.format_name)

# Backward compatibility wrapper
# ✅ FIX 3: Added missing colon in type hint
def generate_dynamic_report(report_data: Dict[str, Any], output_dir: str | Path = ".", filename: str = "architectural_report.md") -> str:
    gen = MarkdownReportGenerator()
    res = gen.render(report_data, Path(output_dir), filename)
    return res.content