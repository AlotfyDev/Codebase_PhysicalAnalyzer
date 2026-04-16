# ports/export.py
"""
[Contract: 04-Abstraction] Export Strategy Protocol.
Pure interface. Zero dependencies. Guarantees swapability for CSV/PSQL/HDF5/Parquet.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Dict, Any, runtime_checkable

@dataclass
class ExportReport:
    success: bool
    format_name: str
    files_created: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

@runtime_checkable
class IExportStrategy(Protocol):
    """
    [Contract: Strategy Pattern]
    Concrete exporters MUST implement this protocol.
    Enables zero-downtime format swapping and isolated unit testing.
    """
    @property
    def format_name(self) -> str: ...
    
    def export(self, dataframes: Dict[str, Any], output_dir: Path, **kwargs) -> ExportReport: ...
    
    def validate_schema(self, df: Any) -> bool:
        """Optional pre-export validation hook."""
        return "schema_version" in df.columns and len(df.columns) > 1