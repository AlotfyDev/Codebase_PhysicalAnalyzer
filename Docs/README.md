# Physical Analyzer - Documentation

Welcome to the Physical Analyzer documentation. This folder contains comprehensive documentation for understanding, configuring, and using the Physical Analyzer system.

## Documentation Structure

```
Docs/
├── ARCHITECTURE.md          # System architecture and design
├── CATALOG.md               # Component inventory and interfaces
├── USAGE.md                 # Usage guide and examples
├── README.md                # This file - index and navigation
└── diagrams/                # Standalone Mermaid diagrams
    ├── system-overview.mmd
    ├── domain-pipeline.mmd
    ├── ports-interfaces.mmd
    └── reporting-flow.mmd
```

## Quick Start

### Run Analysis

```python
from application.api import run_analysis

result = run_analysis(
    root_path="/path/to/project",
    config_overrides={}
)

# Output: extraction_dict compatible with Graphify
```

### CLI Usage

```powershell
python -c "from application.runner import main; exit(main(root_path='.', output_dir='./reports'))"
```

## Documentation Guide

| Document | Audience | Purpose |
|----------|----------|---------|
| **ARCHITECTURE.md** | Architects, Developers | System design, layers, data flow, diagrams |
| **CATALOG.md** | Developers, Integrators | Component inventory, interfaces, API |
| **USAGE.md** | Users, DevOps, CI/CD | CLI reference, code examples, config |

## Key Concepts

### Domain Pipeline (5 Stages)

1. **Scanner** (`domain/scanner.py`) - Filesystem traversal with ignore patterns
2. **Metrics** (`domain/metrics.py`) - Depth, weight, entropy calculation
3. **Classifier** (`domain/classifier.py`) - File identity and layer classification
4. **Import Extractor** (`domain/import_extractor.py`) - Multi-language import extraction
5. **Graph Builder** (`domain/graph_builder.py`) - Node/edge generation, impact analysis

### Interfaces (Ports Layer)

- `IPhysicalStage` - Pipeline stage contract
- `IInsightExtractor` - Insight detection contract
- `IReportAggregator` - Report orchestration contract
- `IExportStrategy` / `IImportStrategy` - Data I/O contracts

### Graphify Integration

The Physical Analyzer extends Graphify's extraction pipeline:

```python
from graphify.extract import extract

result = extract(
    paths=[...],
    config={"enable_physical_analysis": True}
)
```

## Health Score

The system calculates a health score (0-100) based on insights:

| Score | Status | Exit Code |
|-------|--------|-----------|
| >= 80 | Healthy | 0 |
| 60-79 | Warnings | 1 |
| < 60 | Critical | 2 |
| N/A | Runtime Error | 3 |

## Common Tasks

### Generate Reports

```python
from application.runner import main

main(
    root_path=".",
    output_dir="./reports",
    config={"generate_markdown": True}
)
```

### Configure Thresholds

```python
config = {
    "aggregator": {
        "thresholds": {
            "max_depth": 8,
            "cycles_allowed": 0
        }
    }
}
```

### Integrate with CI/CD

```python
import sys
from application.runner import main

exit_code = main(root_path=".", output_dir="./reports")
sys.exit(exit_code)  # 0/1/2/3 based on health
```

## Diagrams

Mermaid diagram files are stored in `diagrams/`:

- `system-overview.mmd` - Complete system architecture
- `domain-pipeline.mmd` - 5-stage domain pipeline
- `ports-interfaces.mmd` - Interface hierarchy
- `reporting-flow.mmd` - Insight extraction flow

## Related Documentation

- [Graphify README](../../graphify_src/README.md) - Graphify integration details
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detailed architecture
- [CATALOG.md](./CATALOG.md) - Component reference
- [USAGE.md](./USAGE.md) - Complete usage guide

## Version

Current version: See `__init__.py` or Git tags.

---

For questions or issues, please refer to the GitHub repository.