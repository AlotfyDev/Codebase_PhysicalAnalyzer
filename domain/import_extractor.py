# domain/import_extractor.py
"""
Domain Stage P-03: Lightweight Import Extraction & Path Resolution.
Pure regex & resolution logic. Reads file content, extracts imports, resolves paths.
Maps to: engines/file_processor.py (P-03, _extract_imports, _resolve_import_path)
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from domain.types import AnalysisContext, ImportTarget, StageResult
from ports.stage import IPhysicalStage

# [Contract: P-03] Precompiled lightweight import patterns per extension
IMPORT_REGEX: Dict[str, re.Pattern] = {
    ".py": re.compile(r"^\s*(?:import\s+([\w.]+)|from\s+([\w.]+)\s+import)", re.MULTILINE),
    ".js": re.compile(r"^\s*(?:import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\s*\(\s*['\"]([^'\"]+)['\"]\s*\))", re.MULTILINE),
    ".ts": re.compile(r"^\s*(?:import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\s*\(\s*['\"]([^'\"]+)['\"]\s*\))", re.MULTILINE),
    ".java": re.compile(r"^\s*import\s+([\w.]+(?:\.\*)?)\s*;", re.MULTILINE),
    ".go": re.compile(r"^\s*(?:\"([^\"]+)\"|import\s*\([\s\S]*?\"([^\"]+)\"[\s\S]*?\))", re.MULTILINE),
    ".c": re.compile(r"^\s*#include\s*[\"<]([^\">]+)[\">]", re.MULTILINE),
    ".cpp": re.compile(r"^\s*#include\s*[\"<]([^\">]+)[\">]", re.MULTILINE),
    ".rb": re.compile(r"^\s*require\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    ".php": re.compile(r"^\s*(?:require|include)\s*['\"]([^'\"]+)['\"]", re.MULTILINE),
}

SUPPORTED_EXTENSIONS = set(IMPORT_REGEX.keys())


class ImportExtractorStage(IPhysicalStage):
    """[Contract: 04-IPhysicalStage] Executes P-03 (Import Extraction & Resolution)."""

    @property
    def stage_id(self) -> str: return "domain.import_extractor"

    def execute(self, context: AnalysisContext) -> StageResult:
        file_set = context.data.get("file_set", set())
        known_files = set(context.files.keys())
        if not file_set or not known_files:
            return StageResult(success=False, errors=["No files to process. Run previous stages first."])

        root = context.root_path.resolve()

        for file_path in file_set:
            if file_path not in known_files: continue

            try:
                ext = file_path.suffix.lower()
                if ext not in IMPORT_REGEX:
                    context.imports[file_path] = []
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                context.imports[file_path] = self._extract_imports(content, ext, file_path, root, known_files)
            except Exception as exc:
                context.parse_errors.append({"file": str(file_path), "error": str(exc), "type": type(exc).__name__})
                context.imports[file_path] = []

        total_imports = sum(len(v) for v in context.imports.values())
        return StageResult(success=True, data={"imports_extracted": total_imports})

    def _extract_imports(self, content: str, ext: str, source_file: Path, root: Path, known_files: Set[Path]) -> List[ImportTarget]:
        """[Contract: 06-RegexImportExtractor] Line-by-line extraction with resolution."""
        targets: List[ImportTarget] = []
        pattern = IMPORT_REGEX.get(ext)
        if not pattern: return targets

        for i, line in enumerate(content.splitlines(), start=1):
            match = pattern.search(line)
            if not match: continue

            raw = match.group(1) or match.group(2)
            resolved = self._resolve_import_path(raw, source_file, root, known_files)
            targets.append(ImportTarget(
                raw_statement=line.strip(), resolved_path=resolved,
                line_number=i, is_resolved=resolved is not None
            ))
        return targets

    @staticmethod
    def _resolve_import_path(raw: str, source_file: Path, root: Path, known_files: Set[Path]) -> Optional[Path]:
        """[Contract: 06-ImportResolution] Relative/Absolute path resolution & extension fallback."""
        if not raw: return None
        candidate = (source_file.parent / raw).resolve() if raw.startswith((".", "..")) else (root / raw).resolve()
        
        if candidate in known_files: return candidate
        for ext in SUPPORTED_EXTENSIONS:
            if candidate.with_suffix(ext) in known_files:
                return candidate.with_suffix(ext)
        return None


__all__ = ["ImportExtractorStage", "IMPORT_REGEX"]