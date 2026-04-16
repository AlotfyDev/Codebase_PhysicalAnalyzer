# reporting/extractors/base.py
"""
[Contract: 04-Abstraction] Base contracts & types for all insight extractors.
Pure definitions. Zero dependencies. Enables swapability & config-driven execution.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Protocol, Dict, List, Any, Optional, runtime_checkable

@dataclass
class TraceabilityRecord:
    metric_name: str
    actual_value: Any
    threshold: Any
    status: str  # PASS | WARN | FAIL
    evidence_path: str

@dataclass
class InsightRecord:
    insight_id: str
    category: str
    severity: str  # critical | warning | info
    title: str
    description: str
    evidence: List[str]
    traceability_matrix: List[TraceabilityRecord]
    recommendation: str
    extractor_id: str = ""

@runtime_checkable
class IInsightExtractor(Protocol):
    """
    [Contract: Strategy Pattern]
    All concrete extractors MUST implement this protocol.
    Receives raw graph data + thresholds, returns structured insights.
    """
    @property
    def extractor_id(self) -> str: ...
    @property
    def default_thresholds(self) -> Dict[str, Any]: ...
    def extract(self, raw_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]: ...
    def collect_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optional: returns raw/queryable data before insight generation."""
        return {}

__all__ = ["IInsightExtractor", "InsightRecord", "TraceabilityRecord"]