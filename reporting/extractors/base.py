# reporting/extractors/base.py
"""
[Contract: 05-Stage-Base] Unified base for all Extractors/Detectors.
Provides safe graph traversal, threshold merging, and InsightRecord factory.
"""
from __future__ import annotations
from typing import Dict, List, Any
from ports.insight import IInsightExtractor, InsightRecord, TraceabilityRecord

class BaseExtractor(IInsightExtractor):
    """Abstract base implementing IInsightExtractor with shared utilities."""
    
    @property
    def extractor_id(self) -> str:
        raise NotImplementedError("Subclasses must define extractor_id")
    
    @property
    def default_thresholds(self) -> Dict[str, Any]:
        return {}

    def get_raw_findings(self, raw_: Dict[str, Any]) -> Dict[str, Any]:
        """Override to return queryable raw metrics before thresholding."""
        return {}

    def extract(self, raw_: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]:
        cfg = {**self.default_thresholds, **thresholds}
        return self._extract_impl(raw_, cfg)

    def _extract_impl(self, raw_: Dict[str, Any], cfg: Dict[str, Any]) -> List[InsightRecord]:
        """Subclasses implement actual logic here."""
        raise NotImplementedError("Subclasses must implement _extract_impl")

    # ==================== HELPERS ====================
    @staticmethod
    def _make_insight(
        code: str, category: str, severity: str, title: str, desc: str,
        evidence: List[str], trace: List[TraceabilityRecord], rec: str, eid: str
    ) -> InsightRecord:
        return InsightRecord(code, category, severity, title, desc, evidence, trace, rec, eid)

    @staticmethod
    def _filter_nodes(raw_: Dict, node_type: str) -> List[Dict]:
        return [n for n in raw_.get("nodes", []) if n.get("node_type") == node_type]

    @staticmethod
    def _build_inbound_map(raw_: Dict[str, Any]) -> Dict[str, int]:
        inbound = {}
        for e in raw_.get("edges", []):
            if e.get("relation") == "imports":
                tgt = e.get("target", "")
                inbound[tgt] = inbound.get(tgt, 0) + 1
        return inbound