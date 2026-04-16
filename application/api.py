# application/api.py
"""
Public API Facade: High-level entry points for consumers, CLI, and Graphify integration.
Delegates to PhysicalAnalyzerOrchestrator but guarantees a stable public contract.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional

from application.orchestrator import PhysicalAnalyzerOrchestrator


def run_analysis(root_path: str, config_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    [Contract: Public API - 08-IO-HighLevel]
    Synchronous entry point. Returns Graphify-compatible extraction_dict or raises RuntimeError.
    Designed for: CLI, Module import, Graphify pipeline injection, CI/CD automation.
    """
    orchestrator = PhysicalAnalyzerOrchestrator(Path(root_path), config_overrides)
    result = orchestrator.execute()
    
    if not result.success:
        # Unified error formatting for external consumers
        raise RuntimeError(f"Physical analysis failed: {' | '.join(result.errors)}")
        
    return result.data


def run_analysis_safe(root_path: str, config_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    [Contract: Public API - Fail-Soft Variant]
    Returns result dict even on partial failure. Includes success flag & diagnostics.
    Useful for: CI/CD gates, non-blocking reports, exploratory analysis.
    """
    orchestrator = PhysicalAnalyzerOrchestrator(Path(root_path), config_overrides)
    result = orchestrator.execute()
    
    return {
        "success": result.success,
        "data": result.data,
        "errors": result.errors,
        "warnings": result.warnings,
        "metadata": result.data.get("metadata", {})
    }


__all__ = ["run_analysis", "run_analysis_safe"]