# adapters/loaders/csv_loader.py | Contract: TAX-IMP-01, 08-IO
from __future__ import annotations
from pathlib import Path
from typing import Dict

import pandas as pd
from .base import IFormatLoader, LoadReport

class CSVLoader(IFormatLoader):
    """[Contract: Strategy-CSV] قراءة ملفات CSV مُصدّرة، مع معالجة `NULL`، الترميز، والأنواع"""
    
    @property
    def format_name(self) -> str:
        return "csv"

    def load(self, source: Path) -> LoadReport:
        source = source.resolve()
        report = LoadReport(success=True, dataframes={}, warnings=[])
        schema_ver = None

        if source.is_dir():
            files = list(source.glob("*.csv"))
        elif source.is_file():
            files = [source]
        else:
            return LoadReport(success=False, dataframes={}, warnings=[f"Invalid source path: {source}"])

        for f in files:
            try:
                # na_values=["NULL", "null", "None"] لمطابقة مُصدّر AGG-EXP
                df = pd.read_csv(f, encoding="utf-8-sig", na_values=["NULL", "null", "None"], keep_default_na=False)
                
                # تحويل السلاسل الفارغة إلى NaN صريح
                df.replace("", pd.NA, inplace=True)
                
                tbl_name = f.stem.replace("_schema", "").replace(".csv", "")
                report.dataframes[tbl_name] = df
                report.files_loaded.append(f)
                
                # كشف أول سكيما صالح
                if not schema_ver:
                    schema_ver = self.detect_schema_version(df)
                    
            except Exception as e:
                report.warnings.append(f"Failed to load CSV {f.name}: {str(e)}")
                report.success = False

        report.schema_version = schema_ver
        return report