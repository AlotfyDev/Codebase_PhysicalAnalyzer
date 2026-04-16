
# aggregator/exporters/router.py | [Updated] Contract: 04-Factory
from __future__ import annotations
from pathlib import Path
from typing import Dict, Type

from .base import IFormatExporter, ExportReport
from .csv_exporter import CSVExporter
from .psql_exporter import PSQLExporter
from .hdf5_exporter import HDF5Exporter

# [Contract: 04-Swapability] سجل استراتيجيات قابل للتمديد
EXPORTERS: Dict[str, Type[IFormatExporter]] = {
    "csv": CSVExporter,
    "postgresql": PSQLExporter,
    "psql": PSQLExporter,      # alias
    "hdf5": HDF5Exporter,
}

def get_exporter(format_str: str) -> IFormatExporter:
    fmt = format_str.lower().strip()
    if fmt not in EXPORTERS:
        available = ", ".join(sorted(EXPORTERS.keys()))
        raise ValueError(f"Unsupported format: '{fmt}'. Available: {available}")
    return EXPORTERS[fmt]()

def export_data(dataframes, format_str: str, output_dir: Path, **kwargs) -> ExportReport:
    """نقطة توجيه موحدة تدعم تمرير kwargs ديناميكيًا للمُصدّرات المتخصصة"""
    exporter = get_exporter(format_str)
    return exporter.export(dataframes, output_dir, **kwargs)