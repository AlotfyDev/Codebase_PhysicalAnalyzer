# infrastructure/validator.py
"""
Unified Validation Layer: Graphify Schema Compliance & Relational Reference Integrity.
Pure validation logic. No I/O, no stage orchestration. Maps to:
  - utils/schema_validator.py (Graphify extraction_dict compliance)
  - adapters/validators/reference_checker.py (Relational FK/PK & orphan checks)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from domain.types import NodeType, EdgeRelation, ConfidenceLevel


# =========================================================================
# 1. Graphify Schema Validator (Contract: 08-IO-Schema-Validation)
# =========================================================================
def validate_graphify_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    [Contract: 08-IO-Schema-Validation]
    Validates the final extraction_dict against Graphify's strict schema.
    Checks root keys, node/edge structure, enum values, and referential integrity.
    """
    errors: List[str] = []
    valid_nodes: Set[str] = set()

    # 1. Mandatory root structure
    required_keys = {"nodes", "edges", "metadata"}
    if not required_keys.issubset(data.keys()):
        missing = required_keys - data.keys()
        errors.append(f"Missing root keys: {missing}")
        return False, errors

    # 2. Nodes validation
    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list")
        return False, errors

    for i, node in enumerate(nodes):
        node_id = node.get("id", f"index_{i}")
        if not node.get("id"):
            errors.append(f"Node {i} missing 'id'")
        if not node.get("label"):
            errors.append(f"Node {node_id} missing 'label'")
        if node.get("node_type") not in {nt.value for nt in NodeType}:
            errors.append(f"Node {node_id} invalid 'node_type': {node.get('node_type')}")
        if "physical_meta" not in node or not isinstance(node.get("physical_meta"), dict):
            errors.append(f"Node {node_id} missing or invalid 'physical_meta' dict")
        valid_nodes.add(node.get("id"))

    # 3. Edges validation + Referential Integrity (FK check)
    edges = data.get("edges", [])
    if not isinstance(edges, list):
        errors.append("'edges' must be a list")
    else:
        for i, edge in enumerate(edges):
            if not edge.get("source") or not edge.get("target"):
                errors.append(f"Edge {i} missing 'source' or 'target'")
                continue
            if edge.get("relation") not in {er.value for er in EdgeRelation}:
                errors.append(f"Edge {i} invalid 'relation': {edge.get('relation')}")
            if edge.get("confidence") not in {cl.value for cl in ConfidenceLevel}:
                errors.append(f"Edge {i} invalid 'confidence': {edge.get('confidence')}")
            if edge["source"] not in valid_nodes:
                errors.append(f"Edge {i} broken source ref: {edge['source']}")
            if edge["target"] not in valid_nodes:
                errors.append(f"Edge {i} broken target ref: {edge['target']}")

    # 4. Metadata validation
    meta = data.get("metadata", {})
    if not meta.get("analyzer"):
        errors.append("Metadata missing 'analyzer' version")
    if not meta.get("root_path"):
        errors.append("Metadata missing 'root_path'")

    return len(errors) == 0, errors


# =========================================================================
# 2. Relational Reference Checker (Contract: TAX-IMP-03, 08-IO)
# =========================================================================
@dataclass
class RefCheckReport:
    """Standardized report for relational FK/PK integrity checks."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

def check_references(dataframes: Dict[str, pd.DataFrame]) -> RefCheckReport:
    """
    [Contract: 05-STG-VALIDATE]
    Validates Foreign Keys & orphan references across relational tables.
    Applies Fail-Soft policy: logs violations as warnings, fails only on critical missing IDs.
    """
    if not HAS_PANDAS:
        return RefCheckReport(is_valid=False, errors=["pandas is required for relational reference checking."])
        
    report = RefCheckReport(is_valid=True)
    
    # 1. Collect valid entity IDs
    file_ids: Set[str] = set()
    folder_ids: Set[str] = set()
    
    if "files_identity" in dataframes:
        file_ids = set(dataframes["files_identity"]["file_id"].dropna().unique())
    if "folders_hierarchy" in dataframes:
        folder_ids = set(dataframes["folders_hierarchy"]["folder_id"].dropna().unique())
        
    if not file_ids and not folder_ids:
        report.errors.append("Critical: No valid entity IDs found in files_identity or folders_hierarchy.")
        report.is_valid = False
        return report

    # 2. Check import_dependencies (source/target → files_identity)
    if "import_dependencies" in dataframes:
        imp_df = dataframes["import_dependencies"].dropna(subset=["source_id", "target_id"])
        orphan_src = set(imp_df["source_id"]) - file_ids
        orphan_tgt = set(imp_df["target_id"]) - file_ids
        
        if orphan_src:
            report.warnings.append(f"import_dependencies: {len(orphan_src)} source IDs missing in files_identity.")
        if orphan_tgt:
            report.warnings.append(f"import_dependencies: {len(orphan_tgt)} target IDs missing in files_identity.")
            
        report.stats["import_edges_total"] = len(imp_df)
        report.stats["import_edges_valid"] = len(imp_df) - len(orphan_src) - len(orphan_tgt)

    # 3. Check parent_folder_id (files_identity → folders_hierarchy)
    if "files_identity" in dataframes and "parent_folder_id" in dataframes["files_identity"].columns:
        valid_parents = dataframes["files_identity"]["parent_folder_id"].dropna()
        orphan_parents = set(valid_parents) - folder_ids
        if orphan_parents:
            report.warnings.append(f"files_identity: {len(orphan_parents)} orphan parent_folder_id references.")
        report.stats["files_with_valid_parent"] = len(valid_parents) - len(orphan_parents)

    # 4. Check impact_metrics (file_id → files_identity)
    if "impact_metrics" in dataframes:
        impact_ids = set(dataframes["impact_metrics"]["file_id"].dropna().unique())
        orphan_impact = impact_ids - file_ids
        if orphan_impact:
            report.warnings.append(f"impact_metrics: {len(orphan_impact)} IDs missing in files_identity.")

    if report.errors:
        report.is_valid = False
        
    return report


__all__ = ["validate_graphify_schema", "check_references", "RefCheckReport"]