# ports/import_.py
"""
[Contract: 04-Abstraction] Import Strategy Protocol.
Pure interface. Zero dependencies. Guarantees swapability for CSV/PSQL/HDF5/Parquet.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Dict, Any, Optional, runtime_checkable

@dataclass
class LoadReport:
    success: bool
    dataframes: Dict[str, Any] = field(default_factory=dict)
    schema_version: Optional[str] = None
    files_loaded: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@runtime_checkable
class IImportStrategy(Protocol):
    """
    [Contract: Strategy Pattern]
    Concrete loaders MUST implement this protocol.
    Enables unified ingestion pipeline and schema-version routing.
    """
    @property
    def format_name(self) -> str: ...
    
    def load(self, source: Path) -> LoadReport: ...
    
    @staticmethod
    def detect_schema_version(df: Any) -> Optional[str]:
        if "schema_version" in df.columns and not df.empty:
            return str(df["schema_version"].iloc[0])
        return None