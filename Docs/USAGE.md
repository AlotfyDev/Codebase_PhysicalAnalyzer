# Physical Analyzer - Usage Guide

## Table of Contents
1. [CLI Usage](#1-cli-usage)
2. [Python API](#2-python-api)
3. [Configuration](#3-configuration)
4. [Graphify Integration](#4-graphify-integration)
5. [CI/CD Integration](#5-cicd-integration)
6. [Output Formats](#6-output-formats)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. CLI Usage

### Basic Command

```powershell
python -c "from application.runner import main; exit(main(root_path='.', output_dir='./reports', config={'generate_markdown': True}))"
```

### Equivalent via module import

```python
from application.runner import main

exit_code = main(
    root_path=".",
    output_dir="./reports",
    config={"generate_markdown": True}
)
```

### Command-Line Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root_path` | str | `.` | Target directory to analyze |
| `output_dir` | str | `./reports` | Output directory for reports |
| `config` | dict | `{}` | Configuration overrides |

### Exit Codes

| Exit Code | Meaning | Health Score |
|-----------|---------|--------------|
| **0** | Healthy | >= 80 |
| **1** | Warnings | 60-79 |
| **2** | Critical | < 60 |
| **3** | Runtime Error | N/A (exception) |

---

## 2. Python API

### 2.1 Primary Entry Point

```python
from application.api import run_analysis

# Run analysis and get extraction_dict
result = run_analysis(
    root_path="/path/to/project",
    config_overrides={
        "layer_rules": {"src/*": "core"},
        "max_file_size_mb": 10
    }
)

# result is a dict with keys:
# - nodes: List[dict]
# - edges: List[dict]
# - metadata: dict
# - aggregated_metrics: dict
```

### 2.2 Safe Variant (Fail-Soft)

```python
from application.api import run_analysis_safe

result = run_analysis_safe(
    root_path="/path/to/project",
    config_overrides={"max_file_size_mb": 5}
)

# Always returns dict, never raises:
# {
#     "success": bool,
#     "data": dict,        # extraction_dict or {}
#     "errors": List[str],
#     "warnings": List[str],
#     "metadata": dict
# }
```

### 2.3 Direct Orchestrator Usage

```python
from application.orchestrator import PhysicalAnalyzerOrchestrator
from pathlib import Path

orchestrator = PhysicalAnalyzerOrchestrator(
    root_path=Path("/path/to/project"),
    config_overrides={"max_file_size_mb": 5}
)

stage_result = orchestrator.execute()

if stage_result.success:
    graph_data = stage_result.data
    print(f"Nodes: {len(graph_data['nodes'])}")
    print(f"Edges: {len(graph_data['edges'])}")
else:
    print(f"Errors: {stage_result.errors}")
```

### 2.4 Runner with Full Control

```python
from application.runner import PhysicalAnalyzerRunner
from pathlib import Path

runner = PhysicalAnalyzerRunner(config={
    "generate_markdown": True,
    "aggregator": {
        "thresholds": {
            "max_depth": 8,
            "cycles_allowed": 0
        }
    }
})

report = runner.run(
    root_path="/path/to/project",
    output_dir="./reports",
    config_overrides={"max_file_size_mb": 10}
)

print(f"Health Score: {report['metadata']['health_score']}")
print(f"Insights: {len(report['insights'])}")
```

---

## 3. Configuration

### 3.1 Default Configuration

```python
DEFAULT_CONFIG = {
    "layer_rules": {
        "src/*": "core",
        "tests/*": "test",
        "*/__pycache__/*": "external"
    },
    "weight_coeffs": {
        "density": 0.5,
        "depth_penalty": 0.3,
        "centrality": 0.2
    },
    "max_file_size_mb": 5,
    "ignore_patterns": [".git", "__pycache__", "*.pyc", "node_modules"]
}
```

### 3.2 Aggregator Configuration

```python
AGG_CONFIG = {
    "thresholds": {},
    "threshold_overrides": {
        "max_depth": 8,
        "cycles_allowed": 0,
        "unresolved_warn": 3
    },
    "health_penalties": {
        "critical": 20,
        "warning": 10,
        "info": 5
    }
}
```

### 3.3 .graphifyignore Format

Create `.graphifyignore` in the target directory:

```
# Ignore patterns (fnmatch-style)
__pycache__/
*.pyc
.git/
node_modules/
venv/
.env
*.log
```

---

## 4. Graphify Integration

### 4.1 Activation via Config

The Physical Analyzer integrates with Graphify via the `extract()` function's config parameter:

```python
from graphify.extract import extract

result = extract(
    paths=[...],
    cache_root=Path("./graphify-out"),
    config={
        "enable_physical_analysis": True
    }
)

# result["nodes"] now includes physical file/folder nodes
# result["metadata"]["physical_analysis"] contains metadata
```

### 4.2 Manual Pipeline Integration

```python
from application.api import run_analysis
from pathlib import Path

# Step 1: Run Physical Analyzer
physical_data = run_analysis("/path/to/project")

# Step 2: Use with existing Graphify pipeline
# The extraction_dict is compatible with Graphify's build.py
print(f"Physical nodes: {len(physical_data['nodes'])}")
print(f"Physical edges: {len(physical_data['edges'])}")
```

### 4.3 Graphify CLI with Physical Analysis

After Graphify integration is active:

```bash
# Graphify automatically includes Physical Analyzer when enabled
graphify .
# or
graphify --codebase-report /path/to/project
```

---

## 5. CI/CD Integration

### 5.1 Python Script Example

```python
#!/usr/bin/env python
"""CI/CD integration script for Physical Analyzer."""
import sys
from application.runner import main

if __name__ == "__main__":
    exit_code = main(
        root_path=sys.argv[1] if len(sys.argv) > 1 else ".",
        output_dir=sys.argv[2] if len(sys.argv) > 2 else "./reports",
        config={"generate_markdown": True}
    )
    sys.exit(exit_code)
```

### 5.2 GitHub Actions Example

```yaml
name: Code Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Physical Analyzer
        run: |
          python -c "
          from application.runner import main
          exit(main(
              root_path='.',
              output_dir='./reports',
              config={'generate_markdown': True}
          ))
          "
      
      - name: Upload Reports
        uses: actions/upload-artifact@v4
        with:
          name: analysis-reports
          path: reports/
```

### 5.3 Exit Code Handling

```python
import sys
from application.runner import main

exit_code = main(
    root_path=".",
    output_dir="./reports",
    config={"generate_markdown": True}
)

# Example handling
if exit_code == 0:
    print("✅ Analysis passed - healthy codebase")
elif exit_code == 1:
    print("⚠️ Analysis passed - warnings detected")
    sys.exit(1)  # Optionally fail on warnings
elif exit_code == 2:
    print("❌ Analysis failed - critical issues")
    sys.exit(2)
elif exit_code == 3:
    print("🔴 Runtime error occurred")
    sys.exit(3)
```

---

## 6. Output Formats

### 6.1 JSON Report Structure

```json
{
  "metadata": {
    "health_score": 85.5,
    "total_nodes": 150,
    "total_edges": 320,
    "analysis_timestamp": "2026-04-16T12:00:00Z"
  },
  "insights": [
    {
      "insight_id": "STR-001",
      "category": "structure_depth",
      "severity": "info",
      "title": "Average Folder Depth",
      "description": "Average depth across all folders: 3.2",
      "evidence": ["src/core/", "src/utils/"],
      "traceability_matrix": [
        {
          "metric_name": "avg_depth",
          "actual_value": 3.2,
          "threshold": 5.0,
          "status": "PASS",
          "evidence_path": "aggregated_metrics"
        }
      ],
      "recommendation": "Structure is well-balanced",
      "extractor_id": "structure"
    }
  ]
}
```

### 6.2 Markdown Report

Generated automatically when `generate_markdown: True`:

```markdown
# Physical Analyzer Report

## Health Score: 85.5

## Insights Summary

| Category | Severity | Count |
|----------|----------|-------|
| structure_depth | info | 5 |
| circular_deps | critical | 2 |
| impact_analysis | warning | 3 |

## Detailed Insights

### STR-001: Average Folder Depth
- **Severity**: info
- **Description**: Average depth across all folders: 3.2
- **Recommendation**: Structure is well-balanced
```

### 6.3 Extraction Dict (Graphify Format)

```python
{
    "nodes": [
        {
            "id": "fs:folder:src",
            "label": "src",
            "node_type": "physical_folder",
            "source_file": null,
            "physical_meta": {
                "depth": 1,
                "layer": "core",
                "file_count": 15,
                "subfolder_count": 3,
                "weight_score": 0.75
            }
        },
        {
            "id": "fs:file:src:main:py",
            "label": "main.py",
            "node_type": "physical_file",
            "source_file": "src/main.py",
            "physical_meta": {
                "depth": 2,
                "layer": "core",
                "extension": ".py",
                "size_bytes": 4096
            }
        }
    ],
    "edges": [
        {
            "source": "fs:folder:src",
            "target": "fs:file:src:main:py",
            "relation": "contains",
            "confidence": "EXTRACTED"
        }
    ],
    "metadata": {
        "analyzer": "physical_v1",
        "root_path": "/path/to/project",
        "timestamp": "2026-04-16T12:00:00Z"
    },
    "aggregated_metrics": {
        "entry_point_candidates": ["fs:file:src:main:py"],
        "circular_dependencies": [],
        "total_nodes": 150,
        "total_edges": 320,
        "parse_errors_count": 0
    }
}
```

---

## 7. Troubleshooting

### 7.1 Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `NameError: name 'Dict' is not defined` | Missing typing import | Add `from typing import Dict, List, Any` |
| `SyntaxError: invalid syntax` | Missing colon in type annotation | Check `param: Type` format |
| `NameError: name 'raw_data' is not defined` | Variable name mismatch | Use `raw_` consistently |
| `ModuleNotFoundError` | Missing dependencies | Run `pip install -r requirements.txt` |

### 7.2 Performance Optimization

```python
# Limit file size to improve performance
config = {"max_file_size_mb": 1}  # Skip files > 1MB

# Use ignore patterns to skip irrelevant directories
config = {"ignore_patterns": ["node_modules", "__pycache__", ".git"]}
```

### 7.3 Debug Mode

```python
import logging

logging.basicConfig(level=logging.DEBUG)

from application.api import run_analysis
result = run_analysis("/path/to/project")
```

---

## Quick Reference

### Import All You Need

```python
# Primary API
from application.api import run_analysis, run_analysis_safe

# Runner with exit codes
from application.runner import main, PhysicalAnalyzerRunner

# Orchestrator (advanced)
from application.orchestrator import PhysicalAnalyzerOrchestrator

# Domain stages (if needed)
from domain.scanner import ScannerStage
from domain.metrics import MetricsStage
from domain.classifier import ClassifierStage
from domain.import_extractor import ImportExtractorStage
from domain.graph_builder import GraphBuilderStage

# Reporting
from reporting.aggregators.aggregator import InsightAggregator
from reporting.extractors.structure import StructureExtractor
from reporting.extractors.dependency import DependencyExtractor
from reporting.extractors.impact import ImpactExtractor
```

---

## Next Steps

- See [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview
- See [CATALOG.md](./CATALOG.md) for component inventory