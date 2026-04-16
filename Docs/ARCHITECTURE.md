# Physical Analyzer - Architecture Documentation

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Architectural Layers](#2-architectural-layers)
3. [Domain Pipeline](#3-domain-pipeline)
4. [Ports & Interfaces](#4-ports--interfaces)
5. [Adapters Layer](#5-adapters-layer)
6. [Application Orchestration](#6-application-orchestration)
7. [Reporting Pipeline](#7-reporting-pipeline)
8. [Graphify Integration](#8-graphify-integration)
9. [Data Flow](#9-data-flow)
10. [Configuration & Schema](#10-configuration--schema)

---

## 1. System Overview

### Purpose
Physical Analyzer is a codebase structure analysis tool that extracts physical file hierarchy, computes structural metrics, and generates Graphify-compatible knowledge graphs. It integrates with Graphify to enrich semantic understanding with physical filesystem context.

### Core Capabilities
- **Filesystem Traversal**: BFS/DFS with ignore pattern filtering
- **Structural Metrics**: Depth, weight scores, entropy calculation
- **Import Extraction**: Multi-language import resolution (Python, JS, Go, Java, etc.)
- **Graph Building**: Nodes/edges generation compatible with Graphify schema
- **Insight Detection**: Architecture health scoring, dependency analysis, impact analysis
- **Report Generation**: Markdown, JSON, HTML outputs

---

## 2. Architectural Layers

```mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI: python -m]
        API[Python API]
        GRAPHIFY[Graphify Integration]
    end

    subgraph "Application Layer"
        ORCH[Orchestrator]
        API_MOD[api.py]
        RUNNER[runner.py]
        BRIDGE[relational_bridge.py]
    end

    subgraph "Domain Layer"
        SCANNER[scanner.py]
        METRICS[metrics.py]
        CLASSIFIER[classifier.py]
        IMPORTS[import_extractor.py]
        GRAPH[graph_builder.py]
    end

    subgraph "Ports Layer"
        STAGE[stage.py]
        CONFIG[config.py]
        EXPORT[export.py]
        IMPORT[import_.py]
        REPORT[report.py]
        INSIGHT[insight.py]
    end

    subgraph "Adapters Layer"
        AD_EXP[export/]
        AD_IMP[import_/]
        AD_CFG[config/]
        AD_GRP[graphify/]
    end

    subgraph "Infrastructure"
        VALID[validator.py]
        SCHEMA[schemas/]
        UTILS[utils.py]
    end

    subgraph "Reporting"
        GEN[generator.py]
        EXT[extractors/]
        AGG[aggregators/]
    end

    CLI --> ORCH
    API --> API_MOD
    GRAPHIFY --> ORCH
    
    ORCH --> STAGE
    STAGE --> SCANNER
    STAGE --> METRICS
    STAGE --> CLASSIFIER
    STAGE --> IMPORTS
    STAGE --> GRAPH
    
    SCANNER --> AD_CFG
    GRAPH --> VALID
    GRAPH --> SCHEMA
    
    ORCH --> GEN
    GEN --> EXT
    GEN --> AGG
```

### Layer Responsibilities

| Layer | Responsibility | Dependencies |
|-------|---------------|--------------|
| **Domain** | Pure business logic, no I/O | ports (interfaces only) |
| **Ports** | Abstract interfaces/contracts | None (pure typing) |
| **Adapters** | External I/O implementations | ports (implementations) |
| **Application** | Orchestration, workflow coordination | domain, ports, adapters |
| **Infrastructure** | Schema validation, utilities | domain types |
| **Reporting** | Insight extraction, report generation | domain, ports/insight |

---

## 3. Domain Pipeline

The Domain Layer implements a 5-stage pipeline for physical analysis:

```mermaid
flowchart LR
    subgraph "Input"
        ROOT[AnalysisContext]
    end

    subgraph "Stage 1: Scanner"
        S1[F-01: Filesystem<br/>Traversal]
    end

    subgraph "Stage 2: Metrics"
        S2[F-02: Depth Mapping<br/>F-03: Weight Calc<br/>F-04: Entropy]
    end

    subgraph "Stage 3: Classifier"
        S3[P-01: File Identity<br/>P-02: Layer Classification]
    end

    subgraph "Stage 4: Import Extractor"
        S4[P-03: Import Extraction<br/>& Resolution]
    end

    subgraph "Stage 5: Graph Builder"
        S5[F-05: Node/Edge Build<br/>P-04: Impact Analysis<br/>P-05: Cycle Detection]
    end

    subgraph "Output"
        EXTRACT[extraction_dict<br/>Graphify-compatible]
    end

    ROOT --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 --> EXTRACT
```

### Stage Details

| Stage | Module | Contracts | Output |
|-------|--------|-----------|--------|
| **F-01** | `scanner.py` | `IPhysicalStage` | folder_tree, folder_set, file_set |
| **F-02/F-03/F-04** | `metrics.py` | `IPhysicalStage` | depth_map, weight_map, global_entropy |
| **P-01/P-02** | `classifier.py` | `IPhysicalStage` | context.files (FileIdentity) |
| **P-03** | `import_extractor.py` | `IPhysicalStage` | context.imports |
| **F-05/P-04/P-05** | `graph_builder.py` | `IPhysicalStage` | extraction_dict |

### Key Data Structures (domain/types.py)

```mermaid
classDiagram
    class AnalysisContext {
        +Path root_path
        +List[str] ignore_patterns
        +Dict[str, str] layer_rules
        +Dict[str, float] weight_coeffs
        +int max_file_size_mb
        +Dict[Path, FolderMetrics] folders
        +Dict[Path, FileIdentity] files
        +Dict[Path, List[ImportTarget]] imports
        +List[Dict] parse_errors
        +List[str] warnings
    }
    
    class FileIdentity {
        +Path path
        +Path relative_path
        +str name
        +str extension
        +str fs_id
        +int size_bytes
        +LayerType layer
        +int depth
    }
    
    class FolderMetrics {
        +int depth
        +LayerType layer
        +int file_count
        +int subfolder_count
        +float weight_score
        +float entropy_contribution
        +List[str] nesting_chain
        +int path_length
    }
    
    class PhysicalNode {
        +str id
        +str label
        +NodeType node_type
        +str source_file
        +Dict physical_meta
    }
    
    class PhysicalEdge {
        +str source
        +str target
        +EdgeRelation relation
        +ConfidenceLevel confidence
        +Dict meta
    }
    
    AnalysisContext --> FolderMetrics
    AnalysisContext --> FileIdentity
    FileIdentity --> PhysicalNode
    FolderMetrics --> PhysicalNode
```

---

## 4. Ports & Interfaces

The Ports Layer defines abstract contracts (Protocols) for loose coupling:

```mermaid
classDiagram
    direction TB
    
    class IPhysicalStage {
        <<interface>>
        +str stage_id
        +execute(context) StageResult
    }
    
    class IPipeline {
        <<interface>>
        +run(root_path, **kwargs) Any
    }
    
    class IExportStrategy {
        <<interface>>
        +str format
        +export(data, path) None
        +validate(data) bool
    }
    
    class IImportStrategy {
        <<interface>>
        +str format
        +load(path) Dict
        +detect_schema(path) Schema
    }
    
    class IReportGenerator {
        <<interface>>
        +generate(data, output_path) None
        +format_html() str
        +format_markdown() str
    }
    
    class IConfigLoader {
        <<interface>>
        +load(path) Dict
        +save(config, path) None
    }
    
    class IInsightExtractor {
        <<interface>>
        +str extractor_id
        +default_thresholds() Dict
        +get_raw_findings(raw_) Dict
        +extract(raw_data, thresholds) List[InsightRecord]
    }
    
    class IReportAggregator {
        <<interface>>
        +register_extractor(extractor) None
        +execute(raw_data, config) Dict
        +calculate_health(insights, total_nodes, penalties) float
    }
    
    IPhysicalStage <|.. ScannerStage
    IPhysicalStage <|.. MetricsStage
    IPhysicalStage <|.. ClassifierStage
    IPhysicalStage <|.. ImportExtractorStage
    IPhysicalStage <|.. GraphBuilderStage
    
    IInsightExtractor <|.. StructureExtractor
    IInsightExtractor <|.. DependencyExtractor
    IInsightExtractor <|.. ImpactExtractor
    
    IReportAggregator <|.. InsightAggregator
```

### Interface Definitions

#### IPhysicalStage (ports/stage.py)
```python
@runtime_checkable
class IPhysicalStage(Protocol):
    @property
    def stage_id(self) -> str: ...
    
    def execute(self, context: Any) -> StageResult: ...
```

#### IInsightExtractor (ports/insight.py)
```python
@runtime_checkable
class IInsightExtractor(Protocol):
    @property
    def extractor_id(self) -> str: ...
    
    def default_thresholds(self) -> Dict[str, Any]: ...
    
    def get_raw_findings(self, raw_: Dict[str, Any]) -> Dict[str, Any]: ...
    
    def extract(self, raw_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[InsightRecord]: ...
```

---

## 5. Adapters Layer

```mermaid
graph LR
    subgraph "Export Adapters"
        E_CSV[csv.py]
        E_PSQL[psql.py]
        E_HDF5[hdf5.py]
        E_PARQUET[parquet.py]
        E_ROUTER[router.py]
        E_BASE[base.py]
    end
    
    subgraph "Import Adapters"
        I_CSV[csv.py]
        I_SQL[sql.py]
        I_HDF5[hdf5.py]
        I_PARQUET[parquet.py]
        I_ROUTER[router.py]
        I_BASE[base.py]
    end
    
    subgraph "Config Adapters"
        CFG_JSON[json_ignored.py]
    end
    
    subgraph "Graphify Adapters"
        GRP_FLAGS[cli_flags.py]
        GRP_HOOK[pipeline_hook.py]
    end
    
    E_BASE --> E_ROUTER
    E_ROUTER --> E_CSV
    E_ROUTER --> E_PSQL
    E_ROUTER --> E_HDF5
    E_ROUTER --> E_PARQUET
    
    I_BASE --> I_ROUTER
    I_ROUTER --> I_CSV
    I_ROUTER --> I_SQL
    I_ROUTER --> I_HDF5
    I_ROUTER --> I_PARQUET
```

### Adapter Pattern Implementation

**Export Router** (adapters/export/router.py):
```python
class ExportRouter:
    _REGISTRY: Dict[str, Type[IExportStrategy]] = {}
    
    @classmethod
    def register(cls, format: str, strategy_cls: Type[IExportStrategy]):
        cls._REGISTRY[format] = strategy_cls
    
    @classmethod
    def get_exporter(cls, format: str) -> IExportStrategy:
        if format not in cls._REGISTRY:
            raise ValueError(f"Unknown format: {format}. Available: {list(cls._REGISTRY.keys())}")
        return cls._REGISTRY[format]()
```

---

## 6. Application Orchestration

```mermaid
sequenceDiagram
    participant User
    participant Runner
    participant Orchestrator
    participant DomainStages
    participant Aggregator
    participant Generator
    
    User->>Runner: main(root_path, output_dir, config)
    Runner->>Orchestrator: run_analysis(root_path, config)
    
    Orchestrator->>DomainStages: execute() [5 stages]
    DomainStages-->>Orchestrator: extraction_dict
    
    Orchestrator->>Aggregator: execute(graph_data, config)
    Aggregator->>Aggregator: register_extractor(StructureExtractor)
    Aggregator->>Aggregator: register_extractor(DependencyExtractor)
    Aggregator->>Aggregator: register_extractor(ImpactExtractor)
    Aggregator-->>Orchestrator: insights + health_score
    
    Orchestrator->>Generator: generate_dynamic_report(report, output_dir)
    Generator-->>Orchestrator: report.md, report.json
    
    Orchestrator-->>Runner: report dict
    Runner-->>User: exit_code (0/1/2/3)
```

### API Entry Points (application/api.py)

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
    Includes: success flag, data, errors, warnings, metadata.
    """
```

### Runner Exit Codes (application/runner.py)

| Exit Code | Meaning | Condition |
|-----------|---------|-----------|
| 0 | Healthy | health_score >= 80 |
| 1 | Warnings | 60 <= health_score < 80 |
| 2 | Critical | health_score < 60 |
| 3 | Runtime Error | Exception thrown |

---

## 7. Reporting Pipeline

```mermaid
flowchart TB
    subgraph "Input"
        GRAPH[Graph Data<br/>extraction_dict]
    end

    subgraph "Extractors"
        STR[StructureExtractor]
        DEP[DependencyExtractor]
        IMP[ImpactExtractor]
    end

    subgraph "Aggregator"
        REG[Register Extractors]
        EXEC[Execute All]
        MERGE[Merge Insights]
        HEALTH[Calculate Health]
    end

    subgraph "Output"
        JSON[JSON Report]
        MD[Markdown Report]
        HTML[HTML Report]
    end

    GRAPH --> STR
    GRAPH --> DEP
    GRAPH --> IMP
    
    STR --> REG
    DEP --> REG
    IMP --> REG
    
    REG --> EXEC
    EXEC --> MERGE
    MERGE --> HEALTH
    
    HEALTH --> JSON
    HEALTH --> MD
    HEALTH --> HTML
```

### Insight Extractors

| Extractor | Purpose | Key Metrics |
|------------|---------|-------------|
| **StructureExtractor** | File/folder depth, layer distribution, nesting | depth_distribution, layer_counts |
| **DependencyExtractor** | Circular dependencies, unresolved imports | circular_deps, unresolved_count |
| **ImpactExtractor** | Entry point analysis, centrality scores | entry_points, impact_ratios |

### Health Score Calculation (reporting/aggregators/aggregator.py)

```python
def calculate_health(insights: List[InsightRecord], total_nodes: int, penalties: Dict[str, float]) -> float:
    """
    Base health = 100
    - Critical: -20 per issue
    - Warning: -10 per issue
    - Info: -5 per issue
    Returns: 0-100 score
    """
```

---

## 8. Graphify Integration

### Integration Points

```mermaid
flowchart LR
    subgraph "Physical Analyzer"
        PA[orchestrator.py]
        API[api.py]
    end

    subgraph "Graphify"
        EXT[extract.py]
        BUILD[build.py]
        CLUSTER[cluster.py]
    end

    PA -->|"run_analysis()"| EXT
    EXT -->|"config={enable_physical_analysis: true}"| BUILD
    BUILD -->|"extraction_dict"| CLUSTER
    CLUSTER -->|"graph.json"| VIS[Visualization]
```

### Activation (graphify_src/graphify/extract.py)

```python
def extract(paths: list[Path], cache_root: Path | None = None, config: dict | None = None) -> dict:
    """
    Extended with config parameter for Physical Analyzer integration.
    """
    config = config or {}
    
    # Original Graphify extraction
    result = original_extraction_logic(paths)
    
    # Physical Analyzer Extension
    if config.get("enable_physical_analysis", False):
        physical_result = _extract_physical(root=root, enable_physical=True)
        result["nodes"].extend(physical_result.get("nodes", []))
        result["edges"].extend(physical_result.get("edges", []))
        result["metadata"]["physical_analysis"] = {...}
    
    return result
```

---

## 9. Data Flow

```mermaid
flowchart LR
    subgraph "Phase 1: Discovery"
        D1[os.walk traversal]
        D2[Ignore pattern filter]
        D3[Folder tree build]
    end

    subgraph "Phase 2: Analysis"
        A1[BFS depth mapping]
        A2[Weight calculation]
        A3[Entropy calculation]
        A4[Layer classification]
    end

    subgraph "Phase 3: Extraction"
        E1[Regex import parsing]
        E2[Path resolution]
        E3[Cross-file resolution]
    end

    subgraph "Phase 4: Graph Build"
        G1[Node generation]
        G2[Edge generation]
        G3[Impact analysis]
        G4[Cycle detection]
    end

    subgraph "Phase 5: Reporting"
        R1[Insight extraction]
        R2[Health scoring]
        R3[Report generation]
    end

    D1 --> D2 --> D3
    D3 --> A1 --> A2 --> A3 --> A4
    A4 --> E1 --> E2 --> E3
    E3 --> G1 --> G2 --> G3 --> G4
    G4 --> R1 --> R2 --> R3
```

---

## 10. Configuration & Schema

### Configuration Files

| File | Purpose |
|------|---------|
| `adapters/config/json_ignored.py` | Load .graphifyignore patterns |
| `ports/config.py` | Config interface definition |
| `infrastructure/relational_schema_v1.py` | SQL table definitions |
| `infrastructure/graphify_schema_v1.py` | extraction_dict schema |

### Schema Validation (infrastructure/validator.py)

```python
def validate_graphify_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates extraction_dict against Graphify strict schema.
    Checks: root keys, node/edge structure, enum values, referential integrity.
    """
```

---

## Appendix: File Inventory

| Directory | Files | Purpose |
|-----------|-------|---------|
| `domain/` | 6 | Pure business logic, 5-stage pipeline |
| `ports/` | 6 | Abstract interfaces/contracts |
| `adapters/export/` | 6 | Data export strategies |
| `adapters/import_/` | 6 | Data import strategies |
| `adapters/config/` | 1 | Configuration loading |
| `adapters/graphify/` | 2 | Graphify integration |
| `application/` | 7 | Orchestration & API |
| `infrastructure/` | 4 | Validation, schemas, utilities |
| `reporting/` | 8 | Insights & report generation |
| `graphify_src/` | Submodule | Graphify codebase |

---

## Next Steps

- See [CATALOG.md](./CATALOG.md) for detailed component inventory
- See [USAGE.md](./USAGE.md) for CLI reference and examples
- See [diagrams/](./diagrams/) for standalone Mermaid source files