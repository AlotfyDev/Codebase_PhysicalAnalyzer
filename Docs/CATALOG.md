# Physical Analyzer - System Catalog

## Table of Contents
1. [Module Inventory](#1-module-inventory)
2. [Domain Layer Components](#2-domain-layer-components)
3. [Ports Interfaces](#3-ports-interfaces)
4. [Adapters Components](#4-adapters-components)
5. [Application Layer](#5-application-layer)
6. [Infrastructure](#6-infrastructure)
7. [Reporting](#7-reporting)
8. [Graphify Integration](#8-graphify-integration)
9. [Data Types & Enums](#9-data-types--enums)
10. [Configuration Schema](#10-configuration-schema)

---

## 1. Module Inventory

### Root Structure

| Path | Type | Purpose |
|------|------|---------|
| `domain/` | Package | Pure business logic - 5-stage analysis pipeline |
| `ports/` | Package | Abstract interfaces/contracts |
| `adapters/` | Package | External I/O implementations |
| `application/` | Package | Orchestration and workflow |
| `infrastructure/` | Package | Validation, schemas, utilities |
| `reporting/` | Package | Insight extraction and report generation |
| `graphify_src/` | Submodule | Graphify codebase (git submodule) |
| `Docs/` | Folder | Documentation |

---

## 2. Domain Layer Components

### 2.1 domain/types.py
**Purpose**: Core domain types - pure data structures with no I/O.

| Entity | Type | Description |
|--------|------|-------------|
| `NodeType` | Enum | `PHYSICAL_FOLDER`, `PHYSICAL_FILE` |
| `EdgeRelation` | Enum | `CONTAINS`, `IMPORTS`, `SIBLING` |
| `ConfidenceLevel` | Enum | `EXTRACTED`, `INFERRED` |
| `LayerType` | Enum | `CORE`, `MODULE`, `NESTED`, `TEST`, `EXTERNAL`, `UTILITY` |
| `FileIdentity` | Dataclass | Immutable file metadata (path, fs_id, layer, depth) |
| `ImportTarget` | Dataclass | Parsed import with resolution status |
| `FolderMetrics` | Dataclass | Folder structural metrics |
| `PhysicalNode` | Dataclass | Graphify-compatible node entity |
| `PhysicalEdge` | Dataclass | Graphify-compatible edge entity |
| `AnalysisContext` | Dataclass | Shared pipeline state |
| `StageResult` | Dataclass | Standardized stage output |

### 2.2 domain/scanner.py
**Purpose**: F-01 - Filesystem hierarchy traversal and filtering.

```python
class ScannerStage(IPhysicalStage):
    stage_id: str = "domain.scanner"
    
    def execute(self, context: AnalysisContext) -> StageResult:
        """BFS/DFS traversal with ignore pattern filtering"""
```

**Outputs**:
- `folder_tree`: Dict[Path, List[Path]] - parent to children mapping
- `folder_set`: Set[Path] - all discovered folders
- `file_set`: Set[Path] - all discovered files

### 2.3 domain/metrics.py
**Purpose**: F-02/F-03/F-04 - Depth, structural weight, nesting entropy.

```python
class MetricsStage(IPhysicalStage):
    stage_id: str = "domain.metrics"
    
    def execute(self, context: AnalysisContext) -> StageResult:
        """Computes metrics and populates context.folders"""
```

**Functions**:
- `calculate_entropy(file_counts_by_depth)` → float (normalized Shannon entropy)
- `calculate_structural_weight(file_count, max_fc, depth, max_depth, children_count, max_cc, coeffs)` → float

### 2.4 domain/classifier.py
**Purpose**: P-01/P-02 - File identity generation and semantic layer classification.

```python
class ClassifierStage(IPhysicalStage):
    stage_id: str = "domain.classifier"
    
    def execute(self, context: AnalysisContext) -> StageResult:
        """Generates FileIdentity and classifies LayerType"""
```

**Functions**:
- `generate_fs_id(path, root, node_type)` → str (e.g., `fs:file:path:to:file`)
- `classify_layer(relative_path, rules)` → LayerType
- `get_file_size_mb(path)` → float

### 2.5 domain/import_extractor.py
**Purpose**: P-03 - Lightweight import extraction and path resolution.

```python
class ImportExtractorStage(IPhysicalStage):
    stage_id: str = "domain.import_extractor"
    
    def execute(self, context: AnalysisContext) -> StageResult:
        """Extracts imports via regex and resolves paths"""
```

**Supported Languages**: `.py`, `.js`, `.ts`, `.java`, `.go`, `.c`, `.cpp`, `.rb`, `.php`

### 2.6 domain/graph_builder.py
**Purpose**: F-05/P-04/P-05 - Graph assembly, impact analysis, cycle detection.

```python
class GraphBuilderStage(IPhysicalStage):
    stage_id: str = "domain.graph_builder"
    
    def execute(self, context: AnalysisContext) -> StageResult:
        """Builds nodes/edges, computes impact, detects cycles"""
```

**Outputs**: `extraction_dict` - Graphify-compatible format with:
- `nodes`: List[PhysicalNode]
- `edges`: List[PhysicalEdge]
- `metadata`: Analyzer info, timestamps
- `aggregated_metrics`: entry_points, circular_dependencies, totals

---

## 3. Ports Interfaces

### 3.1 ports/stage.py
**Purpose**: Pipeline stage contracts.

```python
@runtime_checkable
class IPhysicalStage(Protocol):
    @property
    def stage_id(self) -> str: ...
    
    def execute(self, context: Any) -> StageResult: ...

@runtime_checkable
class IPipeline(Protocol):
    def run(self, root_path: str, **kwargs) -> Any: ...
```

### 3.2 ports/insight.py
**Purpose**: Insight detection and aggregation contracts.

```python
@dataclass
class TraceabilityRecord:
    metric_name: str
    actual_value: Any
    threshold: Any
    status: str  # PASS | WARN | FAIL
    evidence_path: str

@dataclass
class InsightRecord:
    insight_id: str
    category: str
    severity: str  # critical | warning | info
    title: str
    description: str
    evidence: List[str]
    traceability_matrix: List[TraceabilityRecord]
    recommendation: str
    extractor_id: str = ""

@runtime_checkable
class IInsightExtractor(Protocol):
    @property
    def extractor_id(self) -> str: ...
    def default_thresholds(self) -> Dict[str, Any]: ...
    def get_raw_findings(self, raw_: Dict[str, Any]) -> Dict[str, Any]: ...
    def extract(self, raw_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]: ...

@runtime_checkable
class IReportAggregator(Protocol):
    def register_extractor(self, extractor: IInsightExtractor) -> None: ...
    def execute(self, raw_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    def calculate_health(self, insights: List[InsightRecord], total_nodes: int, penalties: Dict[str, float]) -> float: ...
```

### 3.3 ports/export.py
**Purpose**: Data export strategy contracts.

```python
class IExportStrategy(Protocol):
    @property
    def format(self) -> str: ...
    
    def export(self, data: Dict[str, Any], path: Path) -> None: ...
    def validate(self, data: Dict[str, Any]) -> bool: ...
```

### 3.4 ports/import_.py
**Purpose**: Data import strategy contracts.

```python
class IImportStrategy(Protocol):
    @property
    def format(self) -> str: ...
    
    def load(self, path: Path) -> Dict[str, Any]: ...
    def detect_schema(self, path: Path) -> Dict[str, Any]: ...
```

### 3.5 ports/report.py
**Purpose**: Report generation contracts.

```python
class IReportGenerator(Protocol):
    def generate(self, data: Dict[str, Any], output_path: Path) -> None: ...
    def format_html(self, data: Dict[str, Any]) -> str: ...
    def format_markdown(self, data: Dict[str, Any]) -> str: ...
    def format_json(self, data: Dict[str, Any]) -> str: ...
```

### 3.6 ports/config.py
**Purpose**: Configuration loading contracts.

```python
class IConfigLoader(Protocol):
    def load(self, config_path: Path) -> Dict[str, Any]: ...
    def save(self, config: Dict[str, Any], config_path: Path) -> None: ...
```

---

## 4. Adapters Components

### 4.1 Export Adapters (adapters/export/)

| File | Format | Dependencies |
|------|--------|--------------|
| `base.py` | Base class + Registry | ports.export.IExportStrategy |
| `router.py` | Factory | base.ExportRegistry |
| `csv.py` | CSV | pandas |
| `psql.py` | PostgreSQL | sqlalchemy, psycopg2 |
| `hdf5.py` | HDF5 | pandas, tables |
| `parquet.py` | Parquet | pandas, pyarrow |

**Registry Pattern**:
```python
class ExportStrategyRegistry:
    _strategies: Dict[str, Type[IExportStrategy]] = {}
    
    @classmethod
    def register(cls, format: str, strategy_cls: Type[IExportStrategy]):
        cls._strategies[format] = strategy_cls
    
    @classmethod
    def get(cls, format: str) -> IExportStrategy:
        return cls._strategies[format]()
```

### 4.2 Import Adapters (adapters/import_/)

| File | Format | Dependencies |
|------|--------|--------------|
| `base.py` | Base class + Registry | ports.import_.IImportStrategy |
| `router.py` | Factory | base.ImportRegistry |
| `csv.py` | CSV | pandas |
| `parquet.py` | Parquet | pandas, pyarrow |
| `sql.py` | SQL | sqlalchemy |
| `hdf5.py` | HDF5 | pandas, tables |

### 4.3 Config Adapters (adapters/config/)

| File | Purpose |
|------|---------|
| `json_ignored.py` | Load `.graphifyignore` patterns + JSON config |

### 4.4 Graphify Adapters (adapters/graphify/)

| File | Purpose |
|------|---------|
| `cli_flags.py` | CLI flag definitions for Graphify integration |
| `pipeline_hook.py` | Pipeline injection for Graphify extract() |

---

## 5. Application Layer

### 5.1 application/api.py
**Purpose**: Public API facade.

```python
def run_analysis(root_path: str, config_overrides: Optional[Dict] = None) -> Dict[str, Any]:
    """
    [Contract: Public API - 08-IO-HighLevel]
    Synchronous entry point. Returns Graphify-compatible extraction_dict.
    Raises RuntimeError on failure.
    """

def run_analysis_safe(root_path: str, config_overrides: Optional[Dict] = None) -> Dict[str, Any]:
    """
    [Contract: Public API - Fail-Soft Variant]
    Returns result dict even on partial failure.
    """
```

### 5.2 application/orchestrator.py
**Purpose**: Main pipeline orchestration.

```python
class PhysicalAnalyzerOrchestrator:
    def __init__(self, root_path: Path, config_overrides: Optional[Dict] = None):
        self._stages = [
            ScannerStage(),      # F-01
            MetricsStage(),      # F-02/F-03/F-04
            ClassifierStage(),   # P-01/P-02
            ImportExtractorStage(), # P-03
            GraphBuilderStage()  # F-05/P-04/P-05
        ]
    
    def execute(self) -> StageResult:
        """Sequential stage execution with context propagation"""
```

### 5.3 application/runner.py
**Purpose**: CLI and module entry point.

```python
def main(root_path: str = ".", output_dir: str = ".", config: Optional[Dict] = None) -> int:
    """
    Returns exit code for CI/CD gates:
      0 = Healthy (>=80)
      1 = Warnings (60-79)
      2 = Critical (<60)
      3 = Runtime Error
    """
```

### 5.4 application/relational_bridge.py
**Purpose**: Unifies forward (export) and reverse (import) data flows.

### 5.5 application/safe_merger.py
**Purpose**: Safe merge logic - deduplication, metadata enrichment.

### 5.6 application/strategy_registry.py
**Purpose**: Registry for analysis strategies.

---

## 6. Infrastructure

### 6.1 infrastructure/validator.py
**Purpose**: Schema validation.

```python
def validate_graphify_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates extraction_dict against Graphify strict schema.
    Checks: root keys, node/edge structure, enum values, referential integrity.
    """

def validate_relational_schema(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates DataFrame against relational schema.
    Checks: column types, nullability, primary keys, foreign keys.
    """
```

### 6.2 infrastructure/relational_schema_v1.py
**Purpose**: SQL table definitions for relational export.

### 6.3 infrastructure/graphify_schema_v1.py
**Purpose**: extraction_dict validation schema.

### 6.4 infrastructure/utils.py
**Purpose**: Pure helper functions (path utilities, entropy, etc.).

---

## 7. Reporting

### 7.1 reporting/extractors/base.py
**Purpose**: Base extractor class.

```python
class BaseExtractor(IInsightExtractor):
    @property
    def extractor_id(self) -> str: ...
    @property
    def default_thresholds(self) -> Dict[str, Any]: ...
    def get_raw_findings(self, raw_: Dict[str, Any]) -> Dict[str, Any]: ...
    def extract(self, raw_: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]: ...
    def _extract_impl(self, raw_: Dict[str, Any], cfg: Dict[str, Any]) -> List[InsightRecord]: ...
```

### 7.2 reporting/extractors/structure.py
**Purpose**: File/folder depth analysis, layer distribution.

```python
class StructureExtractor(BaseExtractor):
    extractor_id: str = "structure"
    default_thresholds: dict = {
        "max_depth": 10,
        "max_files_per_folder": 50,
        "layer_distribution_threshold": 0.3
    }
```

### 7.3 reporting/extractors/dependency.py
**Purpose**: Circular dependencies, unresolved imports.

```python
class DependencyExtractor(BaseExtractor):
    extractor_id: str = "dependency"
    default_thresholds: dict = {
        "cycles_allowed": 0,
        "unresolved_warn": 5
    }
```

### 7.4 reporting/extractors/impact.py
**Purpose**: Entry point analysis, centrality scores.

```python
class ImpactExtractor(BaseExtractor):
    extractor_id: str = "impact"
    default_thresholds: dict = {
        "min_impact_ratio": 0.1,
        "entry_point_ratio": 0.05
    }
```

### 7.5 reporting/aggregators/aggregator.py
**Purpose**: Orchestrates extractors, merges insights, calculates health.

```python
class InsightAggregator(IReportAggregator):
    def register_extractor(self, extractor: IInsightExtractor) -> None: ...
    def execute(self, raw_data: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]: ...
    def calculate_health(self, insights: List[InsightRecord], total_nodes: int, penalties: Dict[str, float]) -> float: ...
```

### 7.6 reporting/generator.py
**Purpose**: Jinja2-based report generation.

```python
def generate_dynamic_report(report: Dict, output_dir: Path, filename: str = "report.md"):
    """Generates reports in markdown, HTML, or JSON format using Jinja2 templates"""
```

---

## 8. Graphify Integration

### 8.1 graphify_src/graphify/extract.py
**Purpose**: Extended for Physical Analyzer integration.

```python
def extract(paths: list[Path], cache_root: Path | None = None, config: dict | None = None) -> dict:
    """
    Extended with config parameter:
      config = {"enable_physical_analysis": True}
    """
```

### 8.2 _extract_physical()
**Purpose**: Non-breaking extension function.

```python
def _extract_physical(root: Path, enable_physical: bool = False) -> dict:
    """
    Returns: {"nodes": [], "edges": [], "metadata": {}}
    Fail-Soft: catches ImportError and exceptions, returns empty on failure
    """
```

---

## 9. Data Types & Enums

### Enums (domain/types.py)

```python
class NodeType(str, Enum):
    PHYSICAL_FOLDER = "physical_folder"
    PHYSICAL_FILE = "physical_file"

class EdgeRelation(str, Enum):
    CONTAINS = "contains"
    IMPORTS = "imports"
    SIBLING = "sibling"

class ConfidenceLevel(str, Enum):
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"

class LayerType(str, Enum):
    CORE = "core"
    MODULE = "module"
    NESTED = "nested"
    TEST = "test"
    EXTERNAL = "external"
    UTILITY = "utility"
```

---

## 10. Configuration Schema

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
    "ignore_patterns": [".git", "__pycache__", "*.pyc", "node_modules"]
}
```

### Aggregator Configuration

```python
DEFAULT_AGG_CONFIG = {
    "thresholds": {},
    "threshold_overrides": {},
    "health_penalties": {
        "critical": 20,
        "warning": 10,
        "info": 5
    }
}
```

---

## Appendix: Quick Reference

| Component | Path | Key Class/Function |
|-----------|------|-------------------|
| Scanner | `domain/scanner.py` | `ScannerStage` |
| Metrics | `domain/metrics.py` | `MetricsStage` |
| Classifier | `domain/classifier.py` | `ClassifierStage` |
| Import Extractor | `domain/import_extractor.py` | `ImportExtractorStage` |
| Graph Builder | `domain/graph_builder.py` | `GraphBuilderStage` |
| Orchestrator | `application/orchestrator.py` | `PhysicalAnalyzerOrchestrator` |
| API | `application/api.py` | `run_analysis()` |
| Runner | `application/runner.py` | `main()` |
| Aggregator | `reporting/aggregators/aggregator.py` | `InsightAggregator` |
| Validator | `infrastructure/validator.py` | `validate_graphify_schema()` |

---

## Next Steps

- See [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview and diagrams
- See [USAGE.md](./USAGE.md) for CLI reference and code examples