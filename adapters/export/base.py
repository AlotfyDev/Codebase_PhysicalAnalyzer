# adapters/export/base.py
"""Adapter base for exporters. Strictly implements ports.export.IExportStrategy."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

from ports.export import IExportStrategy, ExportReport

class BaseExporter(IExportStrategy):
    """Thin base providing shared validation & report building. Concrete classes inherit this."""
    
    @property
    def format_name(self) -> str:
        raise NotImplementedError("Concrete exporters must define format_name")

    def export(self, dataframes: Dict[str, Any], output_dir: Path, **kwargs) -> ExportReport:
        output_dir.mkdir(parents=True, exist_ok=True)
        report = ExportReport(success=True, format_name=self.format_name, stats={})
        
        for tbl, df in dataframes.items():
            if not self.validate_schema(df):
                report.warnings.append(f"Schema invalid for {tbl}, skipping.")
                continue
            try:
                path = output_dir / f"{tbl}.{self.format_name}"
                self._write(df, path, **kwargs)
                report.files_created.append(path)
                report.stats[tbl] = len(df)
            except Exception as e:
                report.warnings.append(f"Failed {tbl}: {e}")
                report.success = False
        return report

    def validate_schema(self, df: Any) -> bool:
        """Pre-export validation hook. Matches Protocol signature."""
        if not hasattr(df, "columns"): return False
        return "schema_version" in df.columns and len(df.columns) > 1

    def _write(self, df: Any, path: Path, **kwargs) -> None:
        raise NotImplementedError("Concrete exporters must implement _write()")