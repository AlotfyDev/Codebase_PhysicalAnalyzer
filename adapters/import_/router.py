# adapters/loaders/router.py | Contract: 04-Abstraction, 05-STG-LOAD
from __future__ import annotations
from pathlib import Path
from typing import Dict, Type

from .base import IFormatLoader, LoadReport
from .csv_loader import CSVLoader
from .parquet_loader import ParquetLoader

# [Contract: 04-Swapability] سجل قابل للتمديد
LOADERS: Dict[str, Type[IFormatLoader]] = {
    "csv": CSVLoader,
    "parquet": ParquetLoader,
    # جاهز لـ D-6: "hdf5": HDF5Loader, "sql": SQLLoader
}

def get_loader(format_str: str) -> IFormatLoader:
    fmt = format_str.lower().strip()
    if fmt not in LOADERS:
        available = ", ".join(sorted(LOADERS.keys()))
        raise ValueError(f"Unsupported load format: '{fmt}'. Available: {available}")
    return LOADERS[fmt]()

def load_relational_data(source: Path, format_str: str) -> LoadReport:
    """[Contract: 05-STG-LOAD] نقطة توجيه موحدة للتحميل"""
    loader = get_loader(format_str)
    return loader.load(source)