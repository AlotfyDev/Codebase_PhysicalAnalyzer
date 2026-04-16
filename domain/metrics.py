# domain/metrics.py
"""
Domain Stage F-02 to F-04: Depth, Structural Weight, Nesting Entropy & Layer Classification.
Pure mathematical & classification logic. No I/O, no external dependencies.
Maps to: engines/folder_metrics.py (remaining parts) + utils/helpers.py (math/classify)
"""
from __future__ import annotations
import math
import fnmatch
from pathlib import Path
from typing import Dict, List

from domain.types import AnalysisContext, FolderMetrics, LayerType, StageResult
from ports.stage import IPhysicalStage


def calculate_entropy(file_counts_by_depth: Dict[int, int]) -> float:
    """[Contract: F-04] Normalized Shannon Entropy of file distribution across depths."""
    total = sum(file_counts_by_depth.values())
    if total == 0 or len(file_counts_by_depth) < 2:
        return 0.0
    entropy = -sum((c / total) * math.log2(c / total) for c in file_counts_by_depth.values() if c > 0)
    max_possible = math.log2(len(file_counts_by_depth))
    return round(entropy / max_possible, 4) if max_possible > 0 else 0.0


def calculate_structural_weight(
    file_count: int, max_fc: int, depth: int, max_depth: int,
    children_count: int, max_cc: int, coeffs: Dict[str, float]
) -> float:
    """[Contract: F-03] Heuristic weight based on density, depth penalty, and centrality."""
    density = file_count / max_fc if max_fc > 0 else 0.0
    depth_pen = 1.0 - (depth / max_depth) if max_depth > 0 else 1.0
    centrality = children_count / max_cc if max_cc > 0 else 0.0
    
    raw = (coeffs.get("density", 0.5) * density +
           coeffs.get("depth_penalty", 0.3) * depth_pen +
           coeffs.get("centrality", 0.2) * centrality)
    return round(min(max(raw, 0.0), 1.0), 4)


def classify_layer(relative_path: Path, rules: Dict[str, str]) -> LayerType:
    """[Contract: P-02] Semantic layer classification via glob patterns."""
    path_str = relative_path.as_posix()
    for pattern, layer_name in rules.items():
        if fnmatch.fnmatch(path_str, pattern):
            try:
                return LayerType(layer_name)
            except ValueError:
                return LayerType.MODULE
    if any(kw in path_str.lower() for kw in ("test", "spec")):
        return LayerType.TEST
    return LayerType.MODULE


class MetricsStage(IPhysicalStage):
    """[Contract: 04-IPhysicalStage] Executes F-02, F-03, F-04 using pure domain logic."""

    @property
    def stage_id(self) -> str:
        return "domain.metrics"

    def execute(self, context: AnalysisContext) -> StageResult:
        """[Contract: 04-IPhysicalStage.execute] Computes metrics & populates context.folders."""
        try:
            folder_tree = context.data.get("folder_tree", {})
            file_set = context.data.get("file_set", set())
            folder_set = context.data.get("folder_set", set())
            
            # ✅ FIX: Resolve root identically to ScannerStage to prevent relative_to ValueError
            root = context.root_path.resolve()

            if not folder_set:
                return StageResult(success=False, errors=["No folders to process. Run ScannerStage first."])

            # F-02: Depth Mapping (BFS)
            depth_map: Dict[Path, int] = {root: 0}
            queue: List[Path] = [root]
            while queue:
                current = queue.pop(0)
                for child in folder_tree.get(current, []):
                    depth_map[child] = depth_map[current] + 1
                    queue.append(child)

            # F-03: File Counts & Structural Weights
            file_counts: Dict[Path, int] = {f: 0 for f in folder_set}
            for f in file_set:
                if f.parent in file_counts:
                    file_counts[f.parent] += 1

            max_depth = max(depth_map.values(), default=1)
            max_fc = max(file_counts.values(), default=1)
            max_cc = max((len(v) for v in folder_tree.values()), default=1)

            weight_map: Dict[Path, float] = {}
            for folder, depth in depth_map.items():
                fc = file_counts.get(folder, 0)
                cc = len(folder_tree.get(folder, []))
                weight_map[folder] = calculate_structural_weight(
                    fc, max_fc, depth, max_depth, cc, max_cc, context.weight_coeffs
                )

            # F-04: Nesting Entropy
            files_by_depth: Dict[int, int] = {}
            for f in file_set:
                d = depth_map.get(f.parent, 0) + 1
                files_by_depth[d] = files_by_depth.get(d, 0) + 1
            global_entropy = calculate_entropy(files_by_depth)

            # Populate Context & Compute Nesting Chains
            for folder_path in folder_set:
                # ✅ Safe relative path computation
                try:
                    rel = folder_path.relative_to(root)
                except ValueError:
                    rel = folder_path  # Fallback if not strictly subpath

                final_layer = classify_layer(rel, context.layer_rules) if context.layer_rules else LayerType.MODULE

                # Build nesting chain (pure path traversal)
                chain = []
                curr = folder_path
                while curr != root and curr != curr.parent:
                    chain.append(curr.name)
                    curr = curr.parent
                chain.append(root.name)
                chain.reverse()

                context.folders[folder_path] = FolderMetrics(
                    depth=depth_map.get(folder_path, 0),
                    layer=final_layer,
                    file_count=file_counts.get(folder_path, 0),
                    subfolder_count=len(folder_tree.get(folder_path, [])),
                    weight_score=weight_map.get(folder_path, 0.0),
                    entropy_contribution=global_entropy,
                    nesting_chain=chain,
                    path_length=len(chain)
                )

            context.data.update({
                "depth_map": depth_map, "weight_map": weight_map,
                "file_counts": file_counts, "global_entropy": global_entropy
            })

            return StageResult(success=True, data=context.data)

        except Exception as exc:
            context.parse_errors.append({"stage": self.stage_id, "error": str(exc), "type": type(exc).__name__})
            return StageResult(success=False, errors=[f"Critical failure in {self.stage_id}: {exc}"])


__all__ = ["MetricsStage", "calculate_entropy", "calculate_structural_weight", "classify_layer"]