# reporting/extractors/structure.py
"""Extractor for folder depth, weight, entropy, and structural organization."""
from __future__ import annotations
from typing import Dict, List, Any
from .base import IInsightExtractor, InsightRecord, TraceabilityRecord

class StructureExtractor(IInsightExtractor):
    @property
    def extractor_id(self) -> str: return "structure"
    @property
    def default_thresholds(self) -> Dict[str, Any]:
        return {"max_depth": 5, "folder_weight_god": 0.85, "entropy_warn": 0.6, "flat_folder_files": 10}

    def collect_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        folders = [n for n in raw_data.get("nodes", []) if n.get("node_type") == "physical_folder"]
        return {
            "folder_tree_depths": {f["id"]: f["physical_meta"].get("depth", 0) for f in folders},
            "folder_weights": {f["id"]: f["physical_meta"].get("weight_score", 0.0) for f in folders},
            "global_entropy": raw_data.get("aggregated_metrics", {}).get("global_entropy", 0.0)
        }

    def extract(self, raw_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]:
        insights = []
        cfg = {**self.default_thresholds, **thresholds}
        folders = [n for n in raw_data.get("nodes", []) if n.get("node_type") == "physical_folder"]

        for f in folders:
            meta = f.get("physical_meta", {})
            fid, fname = f.get("id", "unknown"), f.get("label", "unknown")
            depth, weight, fc, sc = meta.get("depth", 0), meta.get("weight_score", 0.0), meta.get("file_count", 0), meta.get("subfolder_count", 0)

            if depth > cfg["max_depth"]:
                insights.append(InsightRecord(f"INS-DEPTH-{len(insights)+1:03d}", "nesting_complexity", "warning",
                    "Excessive Folder Nesting", f"'{fname}' depth ({depth}) > limit ({cfg['max_depth']}).",
                    [fid], [TraceabilityRecord("folder_depth", depth, cfg["max_depth"], "WARN", "nodes[*].physical_meta.depth")],
                    "Flatten hierarchy or apply domain-driven structure.", self.extractor_id))
            if weight > cfg["folder_weight_god"]:
                insights.append(InsightRecord(f"INS-GODF-{len(insights)+1:03d}", "modular_violation", "warning",
                    "Overloaded Folder (God Folder)", f"'{fname}' weight ({weight:.2f}) > threshold.",
                    [fid], [TraceabilityRecord("folder_weight", round(weight,3), cfg["folder_weight_god"], "WARN", "nodes[*].physical_meta.weight_score")],
                    "Split by domain responsibility. Apply Vertical Slices.", self.extractor_id))
            if sc == 0 and fc > cfg["flat_folder_files"]:
                insights.append(InsightRecord(f"INS-FLAT-{len(insights)+1:03d}", "structural_organization", "info",
                    "Flat Folder Structure", f"'{fname}' has {fc} files, 0 subfolders.",
                    [fid], [TraceabilityRecord("file_count", fc, cfg["flat_folder_files"], "PASS", "nodes[*].physical_meta.file_count")],
                    "Group related files into feature subdirectories.", self.extractor_id))

        entropy = raw_data.get("aggregated_metrics", {}).get("global_entropy", 0.0)
        if entropy > cfg["entropy_warn"]:
            insights.append(InsightRecord(f"INS-ENTR-{len(insights)+1:03d}", "structural_chaos", "warning",
                "High Nesting Entropy", f"Entropy {entropy:.2f} indicates irregular distribution.",
                ["root_hierarchy"], [TraceabilityRecord("nesting_entropy", round(entropy,3), cfg["entropy_warn"], "WARN", "aggregated_metrics.global_entropy")],
                "Standardize layering (src/core, src/api, src/utils).", self.extractor_id))
        return insights