# domain/classifier.py
"""
Domain Stage P-01 & P-02: File Identity Generation & Semantic Layer Classification.
Pure path-based logic. Updates context.files with identities & layer assignments.
Maps to: engines/file_processor.py (P-01, P-02) + utils/helpers.py (classify_layer, generate_fs_id)
"""
from __future__ import annotations
import fnmatch
import os
from pathlib import Path
from typing import Dict

from domain.types import AnalysisContext, FileIdentity, LayerType, StageResult
from ports.stage import IPhysicalStage


def generate_fs_id(path: Path, root: Path, node_type: str = "file") -> str:
    """[Contract: P-01] Deterministic filesystem identifier."""
    rel = path.relative_to(root).as_posix().replace("/", ":").replace("\\", ":")
    return f"fs:{node_type}:{rel}"

def classify_layer(relative_path: Path, rules: Dict[str, str]) -> LayerType:
    """[Contract: P-02] Semantic layer classification via glob patterns."""
    path_str = relative_path.as_posix()
    for pattern, layer_name in rules.items():
        if fnmatch.fnmatch(path_str, pattern):
            try: return LayerType(layer_name)
            except ValueError: return LayerType.MODULE
    if any(kw in path_str.lower() for kw in ("test", "spec")):
        return LayerType.TEST
    return LayerType.MODULE

def get_file_size_mb(path: Path) -> float:
    try: return os.path.getsize(path) / (1024 * 1024)
    except OSError: return 0.0


class ClassifierStage(IPhysicalStage):
    """[Contract: 04-IPhysicalStage] Executes P-01 (Identity) & P-02 (Classification)."""

    @property
    def stage_id(self) -> str: return "domain.classifier"

    def execute(self, context: AnalysisContext) -> StageResult:
        file_set = context.data.get("file_set", set())
        if not file_set:
            return StageResult(success=False, errors=["No file_set provided. Run Scanner/Metrics first."])

        root = context.root_path.resolve()

        for file_path in file_set:
            try:
                if get_file_size_mb(file_path) > context.max_file_size_mb:
                    context.parse_errors.append({"file": str(file_path), "error": "Size limit exceeded", "type": "SizeLimit"})
                    continue

                rel_path = file_path.relative_to(root)
                fs_id = generate_fs_id(file_path, root, "file")
                layer = classify_layer(rel_path, context.layer_rules) if context.layer_rules else LayerType.MODULE
                depth = context.data.get("depth_map", {}).get(file_path.parent, 0) + 1

                context.files[file_path] = FileIdentity(
                    path=file_path, relative_path=rel_path,
                    name=file_path.name, extension=file_path.suffix.lower(),
                    fs_id=fs_id, size_bytes=file_path.stat().st_size if file_path.exists() else 0,
                    layer=layer, depth=depth
                )
            except Exception as exc:
                context.parse_errors.append({"file": str(file_path), "error": str(exc), "type": type(exc).__name__})

        return StageResult(success=True, data={"files_mapped": len(context.files)})


__all__ = ["ClassifierStage", "generate_fs_id", "classify_layer", "get_file_size_mb"]