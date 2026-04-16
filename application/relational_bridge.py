# application/relational_bridge.py
"""
[Contract: 07-Orchestration / 08-IO]
Bidirectional bridge between Graphify extraction_dict and Relational Tables.
Forward: graph → DataFrames → ExportStrategy (Registry-driven)
Reverse: ImportStrategy → DataFrames → graph → SafeMerger
Schema-agnostic, version-aware, replaces legacy aggregator/core.py & table_builder.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
except ImportError:
    pd = None  # Deferred runtime check to keep domain pure

from application.strategy_registry import export_registry, import_registry
from application.safe_merger import safe_merge
from infrastructure.validator import validate_graphify_schema
from ports.export import ExportReport
from ports.import_ import LoadReport

logger = logging.getLogger(__name__)
SCHEMA_VERSION = "1.0.0"

class RelationalBridge:
    """
    [Contract: Relational Translation & Routing]
    Central hub for exporting analysis to BI/DB formats and importing back for enrichment.
    Strictly uses Strategy Registries for DI. Zero hard-coded format logic.
    """
    def __init__(self):
        if pd is None:
            raise ImportError("RelationalBridge requires pandas. Install via: pip install pandas")

    # ================= FORWARD: Graph → Relational Export =================
    def forward(self, graph_data: Dict[str, Any], format_str: str,
                output_dir: Path, **kwargs) -> ExportReport:
        """
        [Contract: 05-STG-NORMALIZE & 05-STG-EXPORT]
        Transforms extraction_dict to normalized DataFrames & exports via registry.
        """
        logger.info("🔄 Forward Bridge: graph → %s tables", format_str)
        is_valid, errors = validate_graphify_schema(graph_data)
        if not is_valid:
            raise ValueError(f"Invalid graph_data schema. Cannot export: {errors}")

        dataframes = self._normalize_to_tables(graph_data)
        exporter = export_registry.resolve(format_str)
        return exporter.export(dataframes, output_dir, **kwargs)

    # ================= REVERSE: Relational Import → Graph =================
    def reverse(self, source: Path, format_str: str,
                existing_extractions: Optional[Dict[str, Any]] = None,
                **kwargs) -> Dict[str, Any]:
        """
        [Contract: 05-STG-LOAD & 05-STG-MERGE]
        Imports relational tables, validates FK/PK, translates to graph format, & safely merges.
        """
        logger.info("🔄 Reverse Bridge: %s → graph", format_str)
        importer = import_registry.resolve(format_str)
        load_report: LoadReport = importer.load(source)

        if not load_report.success:
            raise RuntimeError(f"Import failed: {load_report.warnings}")
        if load_report.schema_version != SCHEMA_VERSION:
            logger.warning("Schema version mismatch: %s vs %s. Proceeding with caution.", 
                           load_report.schema_version, SCHEMA_VERSION)

        graph_dict = self._translate_to_graphify(load_report.dataframes)
        existing = existing_extractions or {"nodes": [], "edges": [], "metadata": {}}
        merge_report = safe_merge(graph_dict, existing)

        if not merge_report.success:
            raise RuntimeError(f"Merge failed: {merge_report.warnings}")
        return merge_report.merged_dict

    # ================= Internal Normalization (Table Builder Replacement) =================
    def _normalize_to_tables(self, graph_data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Maps nodes/edges to relational DataFrames matching relational_schema_v1."""
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        # 1. Folders Table
        folders = []
        for n in nodes:
            if n.get("node_type") == "physical_folder":
                m = n.get("physical_meta", {})
                folders.append({
                    "folder_id": n["id"], "folder_name": n["label"],
                    "relative_path": n.get("source_file"),
                    "depth": m.get("depth", 0), "layer": m.get("layer", "nested"),
                    "file_count": m.get("file_count", 0),
                    "subfolder_count": m.get("subfolder_count", 0),
                    "weight_score": m.get("weight_score", 0.0),
                    "entropy_contribution": m.get("entropy_contribution", 0.0),
                    "nesting_chain": str(m.get("nesting_chain", [])),
                    "path_length": m.get("path_length", 0)
                })
        df_folders = pd.DataFrame(folders) if folders else pd.DataFrame(columns=["folder_id"])
        df_folders["schema_version"] = SCHEMA_VERSION

        # 2. Files Table
        files = []
        for n in nodes:
            if n.get("node_type") == "physical_file":
                m = n.get("physical_meta", {})
                files.append({
                    "file_id": n["id"], "file_name": n["label"],
                    "relative_path": n.get("source_file"),
                    "extension": m.get("extension", ""),
                    "depth": m.get("depth", 0), "layer": m.get("layer", "module"),
                    "size_bytes": m.get("size_bytes", 0),
                    "parent_folder_id": self._infer_parent_id(n["id"]),
                    "impact_ratio": m.get("impact_ratio", 0.0),
                    "direct_impact": m.get("direct_impact", 0),
                    "transitive_impact": m.get("transitive_impact", 0),
                    "is_entry_point": m.get("is_entry_point", False),
                    "is_god_file": m.get("is_god_file", False)
                })
        df_files = pd.DataFrame(files) if files else pd.DataFrame(columns=["file_id"])
        df_files["schema_version"] = SCHEMA_VERSION

        # 3. Imports Table
        imports = []
        for e in edges:
            if e.get("relation") == "imports":
                imports.append({
                    "source_id": e["source"], "target_id": e["target"],
                    "line_number": e.get("meta", {}).get("line", 0),
                    "is_resolved": e.get("confidence") == "EXTRACTED",
                    "caller_count": 0, "called_count": 0
                })
        df_imports = pd.DataFrame(imports) if imports else pd.DataFrame(columns=["source_id", "target_id"])
        df_imports["schema_version"] = SCHEMA_VERSION

        # 4. Impact Metrics (Derived view for BI/Analytics)
        df_impact = df_files[["file_id", "direct_impact", "transitive_impact", "impact_ratio", 
                              "is_entry_point", "is_god_file", "schema_version"]].copy()

        return {
            "folders_hierarchy": df_folders,
            "files_identity": df_files,
            "import_dependencies": df_imports,
            "impact_metrics": df_impact
        }

    # ================= Internal Translation (Schema Mapper Replacement) =================
    def _translate_to_graphify(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Reconstructs extraction_dict from relational DataFrames with 1:1 fidelity."""
        nodes, edges = [], []
        df_folders = dataframes.get("folders_hierarchy", pd.DataFrame())
        df_files = dataframes.get("files_identity", pd.DataFrame())
        df_imports = dataframes.get("import_dependencies", pd.DataFrame())

        for _, r in df_folders.iterrows():
            meta = r.drop(["folder_id", "folder_name", "relative_path", "schema_version"], errors="ignore").to_dict()
            nodes.append({
                "id": r["folder_id"], "label": r.get("folder_name", ""),
                "node_type": "physical_folder", "source_file": r.get("relative_path"),
                "physical_meta": meta
            })
        for _, r in df_files.iterrows():
            meta = r.drop(["file_id", "file_name", "relative_path", "schema_version"], errors="ignore").to_dict()
            nodes.append({
                "id": r["file_id"], "label": r.get("file_name", ""),
                "node_type": "physical_file", "source_file": r.get("relative_path"),
                "physical_meta": meta
            })
        for _, r in df_imports.iterrows():
            edges.append({
                "source": r["source_id"], "target": r["target_id"],
                "relation": "imports", 
                "confidence": "EXTRACTED" if r.get("is_resolved") else "INFERRED",
                "meta": {"line": r.get("line_number", 0)}
            })

        return {
            "nodes": nodes, "edges": edges,
            "metadata": {"analyzer": "relational_reverse_v1", "schema_version": SCHEMA_VERSION}
        }

    @staticmethod
    def _infer_parent_id(file_id: str) -> Optional[str]:
        """Heuristic parent inference for reverse translation."""
        parts = file_id.split(":")
        if len(parts) > 3:
            return f"fs:folder:{':'.join(parts[2:-1])}"
        return None

# ================= High-Level API =================
def export_relational(graph_data: Dict, fmt: str, out: str, **kw) -> ExportReport:
    """Convenience wrapper for CLI/Script usage."""
    return RelationalBridge().forward(graph_data, fmt, Path(out), **kw)

def import_relational(src: str, fmt: str, existing: Optional[Dict] = None, **kw) -> Dict:
    """Convenience wrapper for pipeline injection."""
    return RelationalBridge().reverse(Path(src), fmt, existing, **kw)

__all__ = ["RelationalBridge", "export_relational", "import_relational"]