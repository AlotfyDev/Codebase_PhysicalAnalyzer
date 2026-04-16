# Physical Analyzer

[![Python Version](https://img.shields.io/python/version/3.11+-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code_quality-working-brightgreen)](https://github.com/AlotfyDev/Codebase_PhysicalAnalyzer)

Physical Analyzer is a structural codebase analysis module that transforms a repository's **physical filesystem layout** into **Graphify-compatible nodes, edges, metrics, and architecture insights**.

It is designed to complement Graphify by adding **physical hierarchy intelligence**: folders, files, containment relationships, import-level structural dependencies, impact hotspots, and health-oriented reporting.

## Why this project exists

Graphify is strong at building a broader knowledge graph from code and related artifacts. Physical Analyzer focuses on a narrower but important layer:

* the **real folder/file topology** of a codebase
* the **physical import surface** between files
* the **structural shape** of the repository
* the **health signals** that emerge from that layout

In other words:

> **Graphify** helps explain what the system knows.  
> **Physical Analyzer** helps explain how the codebase is physically organized.

## What it produces

Given a project root, Physical Analyzer can generate:

* Graphify-compatible `nodes`
* Graphify-compatible `edges`
* aggregated structural metrics
* architecture insights and health scoring
* report-friendly output for CI/CD and documentation workflows

Typical outputs include:

* physical folder nodes
* physical file nodes
* `contains` edges
* `imports` edges
* structural metrics such as depth, weight, entropy, and cycles
* insight-level findings such as overloaded folders, impact hotspots, and orphan files

## Core capabilities

* Filesystem traversal with ignore-pattern support
* Structural metrics computation (depth, weight, entropy)
* Multi-language lightweight import extraction
* Graphify-compatible graph assembly
* Insight extraction and health scoring
* Report generation (Markdown, JSON) and CI-friendly execution
* Optional Graphify pipeline integration

## Installation

```bash
# Clone the repository
git clone https://github.com/AlotfyDev/Codebase_PhysicalAnalyzer.git
cd Codebase_PhysicalAnalyzer

# Install dependencies
pip install -r requirements.txt
```

### Requirements

```
# Core dependencies
pandas>=2.0.0
jinja2>=3.1.0

# Optional (for export formats)
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
pyarrow>=12.0.0
tables>=3.8.0
```

## Quick start

### Python API

```python
from application.api import run_analysis

result = run_analysis(
    root_path="/path/to/project",
    config_overrides={}
)

print(result.keys())
# dict_keys(["nodes", "edges", "metadata", "aggregated_metrics"])
```

### Python API (Fail-Soft Variant)

```python
from application.api import run_analysis_safe

result = run_analysis_safe(
    root_path="/path/to/project",
    config_overrides={"max_file_size_mb": 10}
)

if result["success"]:
    print(f"Health Score: {result['metadata'].get('health_score', 'N/A')}")
else:
    print(f"Errors: {result['errors']}")
```

### CLI-style execution

```powershell
python -c "from application.runner import main; exit(main(root_path='.', output_dir='./reports'))"
```

## Example output shape

```python
{
    "nodes": [
        {
            "id": "fs:folder:src",
            "label": "src",
            "node_type": "physical_folder",
            "source_file": None,
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
        "root_path": "/path/to/project",
        "timestamp": "2026-04-16T12:00:00Z"
    },
    "aggregated_metrics": {
        "circular_dependencies": [],
        "entry_point_candidates": ["fs:file:src:main:py"],
        "total_nodes": 150,
        "total_edges": 320
    }
}
```

## Graphify integration

Physical Analyzer can be injected into a Graphify-oriented extraction flow when physical analysis is enabled.

```python
from graphify.extract import extract

result = extract(
    paths=[...],
    config={"enable_physical_analysis": True}
)
```

This allows physical nodes, edges, and metadata to be merged into the broader Graphify extraction pipeline.

## Health score

The project computes a health score from extracted insights.

| Score | Status        | Exit Code |
| ----- | ------------- | --------- |
| >= 80 | Healthy       | 0         |
| 60-79 | Warnings      | 1         |
| < 60  | Critical      | 2         |
| N/A   | Runtime Error | 3         |

## Configuration

### Default Configuration

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
    "ignore_patterns": [".git", "__pycache__", "node_modules"]
}
```

### Custom Configuration

Create `graphify-physical.json` in your project root:

```json
{
    "layer_rules": {
        "src/*": "core",
        "modules/*": "module"
    },
    "weight_coeffs": {
        "density": 0.6,
        "depth_penalty": 0.2
    },
    "max_file_size_mb": 10
}
```

### Ignore Patterns

Create `.graphifyignore` in your project root:

```
__pycache__/
*.pyc
.git/
node_modules/
venv/
.env
*.log
```

## Project structure

```
Codebase_PhysicalAnalyzer/
├── domain/              # Pure analysis logic (5-stage pipeline)
│   ├── scanner.py      # F-01: Filesystem traversal
│   ├── metrics.py      # F-02/03/04: Depth, weight, entropy
│   ├── classifier.py   # P-01/02: File identity, layer classification
│   ├── import_extractor.py  # P-03: Import extraction
│   └── graph_builder.py     # F-05/P-04/05: Graph assembly
├── ports/               # Contracts and interfaces
│   ├── stage.py        # IPhysicalStage, IPipeline
│   ├── insight.py      # IInsightExtractor, IReportAggregator
│   ├── export.py       # IExportStrategy
│   └── import_.py      # IImportStrategy
├── adapters/           # External integration layers
│   ├── export/         # CSV, PostgreSQL, HDF5, Parquet
│   ├── import_/        # CSV, SQL, HDF5, Parquet
│   ├── config/         # JSON config loader
│   └── graphify/       # Graphify pipeline integration
├── application/        # Orchestration and public API
│   ├── api.py          # run_analysis(), run_analysis_safe()
│   ├── orchestrator.py # Pipeline orchestration
│   ├── runner.py       # CLI entry point
│   └── safe_merger.py  # Safe graph merge
├── infrastructure/    # Validation and schema helpers
│   ├── validator.py    # Graphify/relational schema validation
│   └── utils.py        # Shared utilities
├── reporting/          # Insights and report generation
│   ├── extractors/     # Structure, Dependency, Impact extractors
│   ├── aggregators/    # InsightAggregator
│   └── generator.py    # Report generation (MD, JSON, HTML)
├── Docs/               # Detailed documentation
│   ├── ARCHITECTURE.md # System architecture
│   ├── CATALOG.md      # Component inventory
│   ├── USAGE.md        # Usage guide
│   └── diagrams/       # Mermaid diagrams
└── tools/              # Utility scripts
```

## Documentation

Detailed documentation lives in `Docs/`.

| Document | Description |
|----------|-------------|
| [`Docs/ARCHITECTURE.md`](Docs/ARCHITECTURE.md) | System architecture and data flow |
| [`Docs/CATALOG.md`](Docs/CATALOG.md) | Component inventory and interfaces |
| [`Docs/USAGE.md`](Docs/USAGE.md) | Usage patterns, examples, and configuration |
| [`Docs/README.md`](Docs/README.md) | Documentation index |
| [`Docs/diagrams/`](Docs/diagrams/) | Mermaid diagram sources |

## Roadmap

- [ ] Add more export formats (Excel, JSON-Lines)
- [ ] Support for additional languages in import extraction
- [ ] Web UI for report visualization
- [ ] Integration with more IDEs via MCP server
- [ ] Performance optimization for large codebases

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See [LICENSE](LICENSE) for details.