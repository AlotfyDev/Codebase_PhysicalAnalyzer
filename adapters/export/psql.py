# aggregator/exporters/psql_exporter.py | Contract: 04-Strategy, 08-IO
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

try:
    import pandas as pd
    from sqlalchemy import create_engine, text
except ImportError as e:
    raise ImportError(f"PSQL export requires pandas & sqlalchemy. Install: pip install pandas sqlalchemy ({e})")

from .base import IFormatExporter, ExportReport

class PSQLExporter(IFormatExporter):
    """[Contract: Strategy-PSQL] تصدير علائقي كامل: DDL تلقائي + INSERT/COPY سريع"""
    
    @property
    def format_name(self) -> str:
        return "postgresql"

    def export(self, dataframes: Dict[str, pd.DataFrame], output_dir: Path, **kwargs: Any) -> ExportReport:
        db_uri = kwargs.get("db_uri")
        schema = kwargs.get("schema", "public")
        if_exists = kwargs.get("if_exists", "replace")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report = ExportReport(success=True, format="postgresql", stats={})
        
        if not db_uri:
            report.warnings.append("No db_uri provided. Generating offline DDL only.")
            
        for tbl_name, df in dataframes.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                report.warnings.append(f"Skipped empty table: {tbl_name}")
                continue
                
            # 1. توليد CREATE TABLE تلقائي (للتوثيق أو التنفيذ اليدوي)
            ddl_path = output_dir / f"{tbl_name}_schema.sql"
            ddl_text = self._generate_ddl(tbl_name, df, schema)
            ddl_path.write_text(ddl_text, encoding="utf-8")
            
            # 2. التصدير الحي لقاعدة البيانات (اختياري)
            if db_uri and self.validate_schema(df):
                try:
                    engine = create_engine(db_uri)
                    df.to_sql(tbl_name, engine, schema=schema, if_exists=if_exists, index=False, method="multi")
                    report.stats[tbl_name] = len(df)
                except Exception as e:
                    report.warnings.append(f"DB insert failed for {tbl_name}: {str(e)}")
                    report.success = False

        if not db_uri:
            report.files_created.append(output_dir / "*_schema.sql")
            
        return report

    @staticmethod
    def _generate_ddl(tbl: str, df: pd.DataFrame, schema: str) -> str:
        """يولد عبارة CREATE TABLE متوافقة مع PostgreSQL من DataFrame schema"""
        cols = []
        for col, dtype in df.dtypes.items():
            if col == "schema_version": continue
            if pd.api.types.is_integer_dtype(dtype):
                sql_type = "BIGINT"
            elif pd.api.types.is_float_dtype(dtype):
                sql_type = "DOUBLE PRECISION"
            elif pd.api.types.is_bool_dtype(dtype):
                sql_type = "BOOLEAN"
            else:
                sql_type = "TEXT"
            cols.append(f"  {col} {sql_type}")
            
        return f"-- Auto-generated DDL for {tbl}\n-- Schema: {schema}\nCREATE TABLE IF NOT EXISTS {schema}.{tbl} (\n{', '.join(cols)}\n);\n"