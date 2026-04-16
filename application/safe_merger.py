# adapters/mergers/safe_merger.py | Contract: TAX-IMP-04, 08-IO, Idempotency
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

@dataclass
class MergeReport:
    success: bool
    merged_dict: Dict[str, Any]
    stats: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

def _deep_update_meta(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """تحديث آمن لـ physical_meta دون فقدان الحقول الأصلية أو كسر الأنواع"""
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            base[k] = _deep_update_meta(base[k], v)
        else:
            base[k] = v
    return base

def safe_merge(relational_dict: Dict[str, Any], existing_dict: Dict[str, Any]) -> MergeReport:
    """
    [Contract: 05-STG-MERGE]
    يدمج العقد/الحواف العلائقية مع استخراج AST موجود بذكاء:
    - يمنع تصادم المعرفات
    - يثري existing nodes بـ physical_meta فقط
    - يتجنب تكرار الحواف المتطابقة
    - يضمن Idempotency (التنفيذ المتكرر يعطي نفس النتيجة)
    """
    merged = deepcopy(existing_dict)
    merged.setdefault("nodes", [])
    merged.setdefault("edges", [])
    merged.setdefault("metadata", {})

    # فهارس سريعة للأداء
    existing_nodes_map = {n["id"]: n for n in merged["nodes"] if "id" in n}
    existing_edges_set: Set[Tuple[str, str, str]] = set()
    for e in merged["edges"]:
        if all(k in e for k in ("source", "target", "relation")):
            existing_edges_set.add((e["source"], e["target"], e["relation"]))

    new_nodes, updated_nodes, added_edges, skipped_edges = 0, 0, 0, 0

    # 1. دمج العقد
    for rel_node in relational_dict.get("nodes", []):
        nid = rel_node.get("id")
        if not nid: continue

        if nid in existing_nodes_map:
            # تحديث آمن: إضافة/تحديث physical_meta فقط، لا نلمس label/source_file/node_type
            existing_node = existing_nodes_map[nid]
            existing_meta = existing_node.setdefault("physical_meta", {})
            _deep_update_meta(existing_meta, rel_node.get("physical_meta", {}))
            updated_nodes += 1
        else:
            merged["nodes"].append(rel_node)
            existing_nodes_map[nid] = rel_node
            new_nodes += 1

    # 2. دمج الحواف
    valid_ids = set(existing_nodes_map.keys())
    for rel_edge in relational_dict.get("edges", []):
        src, tgt, rel = rel_edge.get("source"), rel_edge.get("target"), rel_edge.get("relation")
        edge_key = (src, tgt, rel)

        # تخطي الحواف التي تشير لعقد غير موجودة أو مكررة
        if src not in valid_ids or tgt not in valid_ids or edge_key in existing_edges_set:
            skipped_edges += 1
            continue

        merged["edges"].append(rel_edge)
        existing_edges_set.add(edge_key)
        added_edges += 1

    # 3. دمج البيانات الوصفية
    merged["metadata"].update(relational_dict.get("metadata", {}))
    merged["metadata"]["merge_report"] = {
        "new_nodes": new_nodes, "updated_nodes": updated_nodes,
        "added_edges": added_edges, "skipped_edges": skipped_edges
    }

    return MergeReport(
        success=True, merged_dict=merged,
        stats={"new_nodes": new_nodes, "updated_nodes": updated_nodes, 
               "added_edges": added_edges, "skipped_edges": skipped_edges}
    )