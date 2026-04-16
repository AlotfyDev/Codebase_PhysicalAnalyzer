# application/__init__.py
from .api import run_analysis, run_analysis_safe
from .strategy_registry import export_registry, import_registry, report_registry
from adapters.config.json_ignored import JsonConfigLoader
from adapters.export.base import BaseExporter  # استبدلها بـ CsvExporter الفعلي لاحقًا
from adapters.import_.base import BaseImporter  # استبدلها بـ CsvImporter الفعلي لاحقًا
from reporting.generator import MarkdownReportGenerator


# Config Loader Singleton
config_loader = JsonConfigLoader()


# Register Strategies
report_registry.register("markdown", MarkdownReportGenerator, is_default=True)
# export_registry.register("csv", CsvExporter, is_default=True)  # جاهز للتفعيل
# import_registry.register("csv", CsvImporter, is_default=True)  # جاهز للتفعيل













__all__ = ["run_analysis", "run_analysis_safe"]