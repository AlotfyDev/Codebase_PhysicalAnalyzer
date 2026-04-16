#!/usr/bin/env bash
set -euo pipefail

BRANCH_NAME="${1:-fix/runtime-gaps-and-prune-obsolete}"
COMMIT_MSG="fix: stabilize runtime, unify extractor contract, integrate safe graph merge, and remove obsolete artifacts"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must be run inside a git repository." >&2
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "$BRANCH_NAME" ]]; then
  git checkout -B "$BRANCH_NAME"
fi

rm -f application/run_analysis_Obsolete.py
rm -f reporting/generator_obsolete.py
rm -f reporting/aggregators/aggregator_obsolete.py

python3 <<'PY'
from pathlib import Path


def replace_exact(path_str: str, old: str, new: str):
    path = Path(path_str)
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected snippet not found in {path_str}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

# 1) Fix config loader wiring in orchestrator
replace_exact(
    "application/orchestrator.py",
    '''try:\n    from adapters.config.json_ignored import load_config, load_ignore_patterns\nexcept ImportError:\n''',
    '''try:\n    from adapters.config.json_ignored import JsonConfigLoader\n\n    _cfg_loader = JsonConfigLoader()\n\n    def load_ignore_patterns(root: Path) -> List[str]:\n        return _cfg_loader.load_ignore_patterns(root)\n\n    def load_config(root: Path) -> Dict[str, Any]:\n        return _cfg_loader.load_config(root)\nexcept ImportError:\n'''
)

# 2) Fix aggregator threshold access
replace_exact(
    "reporting/aggregators/aggregator.py",
    'thr = {**ext.default_thresholds, **overrides.get(eid, {})}',
    'thr = {**ext.default_thresholds(), **overrides.get(eid, {})}'
)

# 3) Unify extractor raw findings contract
replace_exact(
    "reporting/extractors/structure.py",
    'def collect_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:',
    'def get_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:'
)
replace_exact(
    "reporting/extractors/impact.py",
    'def collect_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:',
    'def get_raw_findings(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:'
)

# 4) Upgrade Graphify pipeline hook to use safe_merge
pipeline_path = Path("adapters/graphify/pipeline_hook.py")
pipeline_text = pipeline_path.read_text(encoding="utf-8")

old_import = 'from application.api import run_analysis_safe\n'
new_import = 'from application.api import run_analysis_safe\nfrom application.safe_merger import safe_merge\n'
if old_import in pipeline_text and 'from application.safe_merger import safe_merge' not in pipeline_text:
    pipeline_text = pipeline_text.replace(old_import, new_import, 1)

old_merge_block = '''    merged["nodes"].extend(physical_data.get("nodes", []))\n    merged["edges"].extend(physical_data.get("edges", []))\n    merged["metadata"]["physical_analysis"] = physical_data.get("metadata", {})\n    merged["metadata"]["physical_report"] = {\n        "success": result["success"],\n        "errors": result["errors"],\n        "warnings": result["warnings"],\n        "generated_at": physical_data.get("metadata", {}).get("timestamp", "")\n    }\n'''
new_merge_block = '''    merge_result = safe_merge(physical_data, merged)\n    merged = merge_result.merged_dict\n    merged["metadata"]["physical_analysis"] = physical_data.get("metadata", {})\n    merged["metadata"]["physical_report"] = {\n        "success": result["success"],\n        "errors": result["errors"],\n        "warnings": result["warnings"],\n        "generated_at": physical_data.get("metadata", {}).get("timestamp", "")\n    }\n'''
if old_merge_block not in pipeline_text:
    raise SystemExit("Expected merge block not found in adapters/graphify/pipeline_hook.py")
pipeline_text = pipeline_text.replace(old_merge_block, new_merge_block, 1)
pipeline_path.write_text(pipeline_text, encoding="utf-8")
PY

python3 -m compileall application adapters reporting domain infrastructure ports >/dev/null

git add application/orchestrator.py \
        reporting/aggregators/aggregator.py \
        reporting/extractors/structure.py \
        reporting/extractors/impact.py \
        adapters/graphify/pipeline_hook.py \
        tools/apply_runtime_fixes.sh

git add -u

if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

git commit -m "$COMMIT_MSG"

git push -u origin "$BRANCH_NAME"

echo
echo "Done. Branch pushed: $BRANCH_NAME"
