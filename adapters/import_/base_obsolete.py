# adapters/import_/base.py
"""Adapter base for importers. Implements ports.import_.IImportStrategy."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from ports.import_ import IImportStrategy, LoadReport

class BaseImporter(IImportStrategy):
    @property
    def format_name(self) -> str: raise NotImplementedError

    def load(self, source: Path) -> LoadReport:
        report = LoadReport(success=True, format_name=self.format_name, warnings=[])
        try:
            report.dataframes = self._read(source)
            # Detect version from first valid table
            for df in report.dataframes.values():
                ver = self.detect_schema_version(df)
                if ver:
                    report.schema_version = ver
                    break
        except Exception as e:
            report.success = False
            report.warnings.append(str(e))
        return report

    def _read(self, source: Path) -> Dict[str, Any]:
        raise NotImplementedError("Concrete importers must implement _read()")