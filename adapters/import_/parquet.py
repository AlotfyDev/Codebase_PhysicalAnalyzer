# adapters/loaders/parquet_loader.py | Contract: TAX-IMP-01, 08-IO
from __future__ import annotations
from pathlib import Path
from typing import Dict

import pandas as pd
from .base import IFormatLoader, LoadReport

class ParquetLoader(IFormatLoader):
    """[Contract: Strategy-Parquet] قراءة ملفات Parquet مع الحفاظ التام على الأنواع والفهرس الهرمي"""
    
    @property
    def format_name(self) -> str:
        return "parquet"

    def load(self, source: Path) -> LoadReport:
        source = source.resolve()
        report = LoadReport(success=True, dataframes={}, warnings=[])
        schema_ver = None

        if source.is_dir():
            files = list(source.glob("*.parquet"))
        elif source.is_file():
            files = [source]
        else:
            return LoadReport(success=False, dataframes={}, warnings=[f"Invalid source path: {source}"])

        for f in files:
            try:
                df = pd.read_parquet(f, engine="pyarrow")
                tbl_name = f.stem
                report.dataframes[tbl_name] = df
                report.files_loaded.append(f)
                
                if not schema_ver:
                    schema_ver = self.detect_schema_version(df)
                    
            except ImportError:
                return LoadReport(success=False, dataframes={}, 
                                  warnings=["pyarrow not found. Install via: pip install pyarrow pandas"])
            except Exception as e:
                report.warnings.append(f"Failed to load Parquet {f.name}: {str(e)}")
                report.success = False

        report.schema_version = schema_ver
        return report