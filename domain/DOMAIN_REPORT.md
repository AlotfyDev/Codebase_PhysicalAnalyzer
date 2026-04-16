# Domain Layer Architecture Report
# =================================
# Physical Analyzer - Domain Layer Analysis

## 1. Overview

The **domain/** layer is the core of the Physical Analyzer pipeline. It contains pure domain logic with **zero I/O dependencies** - no external file reads, network calls, or database access. All operations work through the `AnalysisContext` shared state.

## 2. File Structure & Purpose

```
domain/
├── types.py          # Core domain entities & enums
├── scanner.py        # F-01: Filesystem traversal
├── classifier.py     # P-01/P-02: File identity & layer classification
├── metrics.py        # F-02/F-03/F-04: Depth, weight, entropy
├── import_extractor.py  # P-03: Import extraction & resolution
└── graph_builder.py     # F-05/P-04/P-05: Graph assembly & analysis
```

## 3. Module Analysis

### 3.1 types.py (Core Types)
**Purpose:** Pure data structures - no logic, no I/O

| Entity | Type | Description |
|--------|------|-------------|
| `NodeType` | Enum | `PHYSICAL_FOLDER`, `PHYSICAL_FILE` |
| `EdgeRelation` | Enum | `CONTAINS`, `IMPORTS`, `SIBLING` |
| `ConfidenceLevel` | Enum | `EXTRACTED`, `INFERRED` |
| `LayerType` | Enum | `CORE`, `MODULE`, `NESTED`, `TEST`, `EXTERNAL`, `UTILITY` |
| `FileIdentity` | Dataclass | Immutable file metadata (path, fs_id, layer, depth) |
| `ImportTarget` | Dataclass | Parsed import with resolution status |
| `FolderMetrics` | Dataclass | Folder structural metrics (depth, weight, entropy) |
| `PhysicalNode` | Dataclass | Graphify-compatible node |
| `PhysicalEdge` | Dataclass | Graphify-compatible edge |
| `AnalysisContext` | Dataclass | Shared pipeline state |
| `StageResult` | Dataclass | Standardized stage output |

### 3.2 scanner.py (F-01)
**Stage:** `ScannerStage`  
**Contract:** `IPhysicalStage`  
**Responsibility:**
- BFS/DFS filesystem traversal via `os.walk()`
- Ignore pattern filtering (`.gitignore` style)
- Produces: `folder_tree`, `folder_set`, `file_set`

**Key Methods:**
- `execute(context)` → StageResult
- `_scan_filesystem(root, ignore_patterns)` → (tree, folders, files)
- `_matches_pattern(name, patterns)` → bool

### 3.3 classifier.py (P-01, P-02)
**Stage:** `ClassifierStage`  
**Contract:** `IPhysicalStage`  
**Responsibility:**
- Generate filesystem IDs (`fs:file:path:to:file`)
- Classify files into semantic layers via glob patterns
- Validate file size limits

**Key Functions:**
- `generate_fs_id(path, root, node_type)` → str
- `classify_layer(relative_path, rules)` → LayerType
- `get_file_size_mb(path)` → float

### 3.4 metrics.py (F-02, F-03, F-04)
**Stage:** `MetricsStage`  
**Contract:** `IPhysicalStage`  
**Responsibility:**
- **F-02:** BFS depth mapping for folders
- **F-03:** Structural weight calculation (density, depth penalty, centrality)
- **F-04:** Shannon entropy of file distribution

**Key Functions:**
- `calculate_entropy(file_counts_by_depth)` → float
- `calculate_structural_weight(file_count, max_fc, depth, max_depth, children_count, max_cc, coeffs)` → float

### 3.5 import_extractor.py (P-03)
**Stage:** `ImportExtractorStage`  
**Contract:** `IPhysicalStage`  
**Responsibility:**
- Regex-based import extraction per language
- Path resolution (relative → absolute, extension fallback)
- Supported: `.py`, `.js`, `.ts`, `.java`, `.go`, `.c`, `.cpp`, `.rb`, `.php`

**Key Components:**
- `IMPORT_REGEX` dict: precompiled patterns per extension
- `_extract_imports(content, ext, source_file, root, known_files)`
- `_resolve_import_path(raw, source_file, root, known_files)`

### 3.6 graph_builder.py (F-05, P-04, P-05)
**Stage:** `GraphBuilderStage`  
**Contract:** `IPhysicalStage`  
**Responsibility:**
- **F-05:** Build nodes (folders + files) with metadata
- **F-05:** Build edges (contains, sibling, imports)
- **P-04:** Reverse BFS impact analysis (entry point detection)
- **P-05:** Cycle detection (DFS-based)
- Output: `extraction_dict` compatible 1:1 with Graphify

**Key Methods:**
- `_build_nodes(context)` → List[PhysicalNode]
- `_build_edges(context)` → List[PhysicalEdge]
- `_compute_reachability_and_cycles(context, nodes, edges)` → (impact_data, cycles)
- `_assemble_final_dict(context, nodes, edges, impact, cycles)` → dict

## 4. Pipeline Flow

```
AnalysisContext (input)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  ScannerStage (F-01)                                        │
│  - Traverse filesystem                                      │
│  - Filter by ignore patterns                                │
│  Output: folder_tree, folder_set, file_set                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  ClassifierStage (P-01, P-02)                               │
│  - Generate FileIdentity                                    │
│  - Classify LayerType                                       │
│  Output: context.files                                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  MetricsStage (F-02, F-03, F-04)                            │
│  - Depth mapping (BFS)                                      │
│  - Structural weight                                        │
│  - Entropy calculation                                      │
│  Output: context.folders                                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  ImportExtractorStage (P-03)                                │
│  - Extract imports via regex                                │
│  - Resolve paths                                            │
│  Output: context.imports                                     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  GraphBuilderStage (F-05, P-04, P-05)                       │
│  - Build nodes & edges                                      │
│  - Impact analysis                                          │
│  - Cycle detection                                          │
│  Output: extraction_dict (Graphify-compatible)              │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
StageResult (output)
```

## 5. Contracts & Interfaces

### 5.1 IPhysicalStage (ports/stage.py)
```python
@runtime_checkable
class IPhysicalStage(Protocol):
    @property
    def stage_id(self) -> str: ...
    
    def execute(self, context: Any) -> Any: ...
```

All domain stages implement this protocol, enabling:
- Structural typing
- Runtime verification
- Dependency injection

### 5.2 Schema Compatibility
- **Nodes:** Compatible with Graphify's `extraction_dict` node schema
- **Edges:** Compatible with Graphify's `extraction_dict` edge schema
- **Output:** Direct 1:1 mapping for graphify-integration

## 6. Key Design Patterns

| Pattern | Usage |
|---------|-------|
| **Dataclass as DTO** | `StageResult`, `AnalysisContext` for state passing |
| **Protocol/Interface** | `IPhysicalStage` for loose coupling |
| **Fail-Soft** | `parse_errors` list in context, not exceptions |
| **Pure Functions** | `calculate_entropy`, `generate_fs_id` - no side effects |
| **Immutable Entities** | `FileIdentity` with `frozen=True` |

## 7. External Dependencies

**None inside domain/** - all imports are from:
- `typing` (standard library)
- `pathlib.Path` (standard library)
- `dataclasses` (standard library)
- `re` (standard library)
- `math` (standard library)
- `ports.stage.IPhysicalStage` (internal contract)

## 8. Summary

The domain layer is a **well-structured, pure business logic layer** that:
1. Implements a 5-stage pipeline (F-01 → F-05, P-01 → P-05)
2. Maintains zero external I/O dependencies
3. Produces Graphify-compatible output (`extraction_dict`)
4. Uses contracts for loose coupling
5. Supports fail-soft error handling
6. Computes depth, weight, entropy, impact, and cycles

This architecture enables testability, maintainability, and clean integration with graphify.