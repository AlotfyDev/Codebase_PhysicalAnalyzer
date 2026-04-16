# aggregator/exporters/csv_exporter.py | Contract: 08-IO, TAX-AGG-08
from __future__ import annotations
from pathlib import Path
from typing import Dict

try:
    import pandas as pd
except ImportError:
    raise ImportError("pandas is required for CSV export.")

from .base import IFormatExporter, ExportReport

class CSVExporter(IFormatExporter):
    """
    [Contract: Strategy-CSV]
    يصدر الجداول كملفات CSV متوافقة مع Excel/PostgreSQL COPY.
    يدعم utf-8-sig، هروب ذكي، وتمثيل صريح للقيم الفارغة.
    """
    @property
    def format_name(self) -> str:
        return "csv"

    def export(self, dataframes: Dict[str, pd.DataFrame], output_dir: Path) -> ExportReport:
        output_dir.mkdir(parents=True, exist_ok=True)
        report = ExportReport(success=True, format="csv", stats={})
        
        for tbl_name, df in dataframes.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                report.warnings.append(f"Skipped empty/invalid table: {tbl_name}")
                continue
            if not self.validate_schema(df):
                report.warnings.append(f"Schema validation failed for {tbl_name}")
                continue
                
            try:
                file_path = output_dir / f"{tbl_name}.csv"
                # utf-8-sig للتوافق مع Excel، na_rep="NULL" للتوافق مع SQL، quoting=QUOTE_ALL للأمان
                df.to_csv(
                    file_path, 
                    index=False, 
                    encoding="utf-8-sig", 
                    na_rep="NULL", 
                    quotechar='"', 
                    quoting=1 
                )
                report.files_created.append(file_path)
                report.stats[tbl_name] = len(df)
            except Exception as e:
                report.warnings.append(f"Export failed for {tbl_name}: {str(e)}")
                report.success = False
                
        return report