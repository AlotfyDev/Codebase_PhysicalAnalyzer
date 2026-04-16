# aggregator/exporters/hdf5_exporter.py | Contract: 04-Strategy, 08-IO
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

try:
    import pandas as pd
except ImportError as e:
    raise ImportError(f"HDF5 export requires pandas. ({e})")

from .base import IFormatExporter, ExportReport

class HDF5Exporter(IFormatExporter):
    """[Contract: Strategy-HDF5] تخزين هرمي مضغوط، قابل للاستعلام الجزئي، أمثل للمشاريع الضخمة"""
    
    @property
    def format_name(self) -> str:
        return "hdf5"

    def export(self, dataframes: Dict[str, pd.DataFrame], output_dir: Path, **kwargs: Any) -> ExportReport:
        try:
            import tables  # Required for pandas HDF5 I/O
        except ImportError:
            return ExportReport(success=False, format="hdf5", warnings=["Missing 'tables' package. Run: pip install tables"])

        output_dir.mkdir(parents=True, exist_ok=True)
        report = ExportReport(success=True, format="hdf5", stats={})
        output_file = output_dir / "relational_export.h5"

        for tbl_name, df in dataframes.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                report.warnings.append(f"Skipped empty table: {tbl_name}")
                continue
            if not self.validate_schema(df):
                report.warnings.append(f"Schema validation failed for {tbl_name}")
                continue

            try:
                # format='table' يسمح بالاستعلام لاحقًا: pd.read_hdf(file, key, where="depth>2")
                df.to_hdf(output_file, key=tbl_name, format="table", 
                          complib="zlib", complevel=5, append=False)
                report.stats[tbl_name] = len(df)
            except Exception as e:
                report.warnings.append(f"HDF5 write failed for {tbl_name}: {str(e)}")
                report.success = False

        if output_file.exists():
            report.files_created.append(output_file)
            
        return report