# domain/scanner.py
"""
Domain Stage F-01: Filesystem Hierarchy Traversal & Filtering.
Pure traversal logic. No I/O, no metrics calculation, no external dependencies.
Maps to: engines/folder_metrics.py (_scan_filesystem) + config.py (ignore pattern application)
"""
from __future__ import annotations
import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ✅ استيراد مطلق مطابق للهيكل الحالي
from domain.types import AnalysisContext, StageResult
from ports.stage import IPhysicalStage


class ScannerStage(IPhysicalStage):
    """
    [Contract: F-01, 04-IPhysicalStage]
    Executes BFS/DFS filesystem traversal, applies ignore patterns in-place,
    and produces raw structural maps for downstream metric/classifier stages.
    """

    @property
    def stage_id(self) -> str:
        return "domain.scanner"

    def execute(self, context: AnalysisContext) -> StageResult:
        """[Contract: 04-IPhysicalStage.execute] Entry point for the scanning stage."""
        try:
            # Execute F-01: Hierarchy Traversal & Filtering
            folder_tree, folder_set, file_set = self._scan_filesystem(
                root=context.root_path,
                ignore_patterns=context.ignore_patterns,
                parse_errors=context.parse_errors
            )
            
            if not folder_set:
                return StageResult(
                    success=False,
                    errors=["No accessible directories found under root."]
                )

            # Pass raw structural data to the shared context for next stages
            context.data.update({
                "folder_tree": folder_tree,
                "folder_set": folder_set,
                "file_set": file_set,
                # Placeholders for F-02/F-03/F-04 stages
                "depth_map": {},
                "layer_map": {},
                "weight_map": {},
                "file_counts": {},
                "global_entropy": 0.0
            })

            return StageResult(success=True, data=context.data)

        except Exception as exc:
            context.parse_errors.append({
                "stage": self.stage_id,
                "error": str(exc),
                "type": type(exc).__name__
            })
            return StageResult(
                success=False,
                errors=[f"Critical failure in {self.stage_id}: {exc}"]
            )

    def _scan_filesystem(
        self, 
        root: Path, 
        ignore_patterns: List[str],
        parse_errors: List[Dict[str, str]]
    ) -> Tuple[Dict[Path, List[Path]], Set[Path], Set[Path]]:
        """
        [Contract: 06-OSWalkScanner] 
        BFS/DFS traversal with in-place ignore filtering.
        Fixed closure scope for error handling compared to legacy version.
        """
        folder_tree: Dict[Path, List[Path]] = {}
        folder_set: Set[Path] = set()
        file_set: Set[Path] = set()
        walk_errors: List[str] = []

        root = root.resolve()
        folder_set.add(root)
        folder_tree.setdefault(root, [])

        def on_error(e: Exception):
            walk_errors.append(f"OS Walk error at {getattr(e, 'filename', 'unknown')}: {str(e)}")

        for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=on_error):
            current_dir = Path(dirpath)
            ignored_dirs = []

            for d in dirnames:
                if self._matches_pattern(d, ignore_patterns):
                    ignored_dirs.append(d)
                else:
                    child = current_dir / d
                    folder_set.add(child)
                    folder_tree.setdefault(current_dir, []).append(child)
                    folder_tree.setdefault(child, [])

            for d in ignored_dirs:
                dirnames.remove(d)

            for f in filenames:
                if not self._matches_pattern(f, ignore_patterns):
                    file_set.add(current_dir / f)

        for err_msg in walk_errors:
            parse_errors.append({"stage": "F-01_OS_WALK", "error": err_msg, "type": "OSError"})

        return folder_tree, folder_set, file_set

    @staticmethod
    def _matches_pattern(name: str, patterns: List[str]) -> bool:
        """[Contract: Pattern Matching] Checks if a file/folder name matches any ignore pattern."""
        return any(fnmatch.fnmatch(name, pat) for pat in patterns)


__all__ = ["ScannerStage"]