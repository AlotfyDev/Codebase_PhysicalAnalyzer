# ports/report.py
"""
[Contract: 04-Abstraction] Report Generator Protocol.
Pure interface. Decouples Jinja2/HTML/JSON rendering from domain logic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Dict, Any, Optional, runtime_checkable

@dataclass
class RenderReport:
    success: bool
    content: str
    output_path: Optional[Path] = None
    warnings: list[str] = field(default_factory=list)
    format_name: str = "markdown"

@runtime_checkable
class IReportGenerator(Protocol):
    """
    [Contract: Strategy Pattern]
    Concrete generators MUST implement this protocol.
    Enables dynamic report switching without pipeline changes.
    """
    @property
    def format_name(self) -> str: ...
    
    def render(self, report_data: Dict[str, Any], output_dir: Path, filename: Optional[str] = None, **kwargs) -> RenderReport: ...