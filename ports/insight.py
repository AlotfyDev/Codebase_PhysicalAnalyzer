# ports/insight.py
"""
[Contract: 04-Abstraction] Unified protocols for Insight Detection, Extraction & Aggregation.
Pure interfaces. Zero dependencies. Guarantees swapability & config-driven execution.
"""
from __future__ import annotations
from dataclasses import dataclass, field
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
    [Contract: Detector/Extractor Strategy]
    Concrete classes MUST implement. Handles raw graph traversal & threshold application.
    """
    @property
    def extractor_id(self) -> str: ...
    def default_thresholds(self) -> Dict[str, Any]: ...
    def get_raw_findings(self, raw_: Dict[str, Any]) -> Dict[str, Any]: ...
    def extract(self, raw_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]: ...

@runtime_checkable
class IReportAggregator(Protocol):
    """
    [Contract: Orchestration Strategy]
    Coordinates extractors, merges findings, calculates health, outputs final report.
    """
    def register_extractor(self, extractor: IInsightExtractor) -> None: ...
    def execute(self, raw_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    def calculate_health(self, insights: List[InsightRecord], total_nodes: int, penalties: Dict[str, float]) -> float: ...