# ports/stage.py
"""
Official contracts (Protocols) for the Physical Analyzer pipeline.
Pure interfaces: no implementation, no external dependencies.
Enables structural typing, runtime checking, and safe dependency injection.
"""
from __future__ import annotations
from typing import Protocol, Any, runtime_checkable

@runtime_checkable
class IPhysicalStage(Protocol):
    """
    [Contract: 04-IPhysicalStage]
    Base protocol for all domain analysis stages.
    Concrete classes MUST implement `stage_id` and `execute`.
    """
    @property
    def stage_id(self) -> str:
        """Unique identifier for this stage (e.g., 'domain.scanner')"""
        ...

    def execute(self, context: Any) -> Any:
        """
        Execute stage logic.
        Receives a shared context (AnalysisContext), returns updated state/result.
        """
        ...

@runtime_checkable
class IPipeline(Protocol):
    """
    [Contract: 04-IPhysicalPipeline]
    Marker protocol for the orchestrator.
    """
    def run(self, root_path: str, **kwargs) -> Any:
        """Execute the full analysis pipeline."""
        ...

__all__ = ["IPhysicalStage", "IPipeline"]