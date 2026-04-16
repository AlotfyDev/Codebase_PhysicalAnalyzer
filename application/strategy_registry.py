# application/strategy_registry.py
"""
[Contract: 07-Orchestration / DI]
Central Strategy Registry. Manages Protocol implementations, validates at registration,
and provides fail-safe resolution. Replaces manual if/elif routing.
"""
from __future__ import annotations
from typing import Type, Dict, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field

@dataclass
class StrategySlot:
    cls: Type
    is_default: bool = False

class StrategyRegistry:
    def __init__(self, protocol: Type[Protocol], name: str = "unknown"):
        self.protocol = protocol
        self.name = name
        self._registry: Dict[str, StrategySlot] = {}
        self.default_format: Optional[str] = None

    def register(self, fmt: str, cls: Type, is_default: bool = False) -> None:
        """Register a concrete implementation. Validates Protocol compliance at runtime."""
        if not runtime_checkable or not isinstance(cls(), self.protocol):
            raise TypeError(f"Class {cls.__name__} does not implement {self.protocol.__name__}")
        
        self._registry[fmt.lower()] = StrategySlot(cls=cls, is_default=is_default)
        if is_default:
            self.default_format = fmt.lower()

    def resolve(self, fmt: Optional[str] = None):
        """Resolve and instantiate strategy. Fails fast if unknown, falls back to default."""
        target = (fmt or self.default_format or "").lower()
        if target not in self._registry:
            available = ", ".join(self._registry.keys())
            raise ValueError(f"Unknown {self.name} format '{fmt}'. Available: {available}")
        return self._registry[target].cls()

    @property
    def supported_formats(self) -> list[str]:
        return list(self._registry.keys())

# 🌐 Global Registries (Module-level Singletons for DI)
export_registry = StrategyRegistry(__import__("ports.export").export.IExportStrategy, "export")
import_registry = StrategyRegistry(__import__("ports.import_").import_.IImportStrategy, "import")
report_registry = StrategyRegistry(__import__("ports.report").report.IReportGenerator, "report")

__all__ = ["export_registry", "import_registry", "report_registry", "StrategyRegistry"]