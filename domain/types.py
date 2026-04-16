# src/graphify/physical_analyzer/domain/types.py
"""
Core domain types: pure data structures, no I/O, no external dependencies.
Defines the fundamental entities, metrics, and shared context for the Physical Analyzer pipeline.
Preserves 100% backward compatibility with legacy extraction_dict schema.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

class NodeType(str, Enum):
    """Standardized node types compatible with Graphify's graph builder."""
    PHYSICAL_FOLDER = "physical_folder"
    PHYSICAL_FILE = "physical_file"

class EdgeRelation(str, Enum):
    """Standardized edge relations for structural & dependency graphs."""
    CONTAINS = "contains"
    IMPORTS = "imports"
    SIBLING = "sibling"

class ConfidenceLevel(str, Enum):
    """Resolution confidence for extracted/imported relationships."""
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"

class LayerType(str, Enum):
    """Semantic classification layers for folders & files."""
    CORE = "core"
    MODULE = "module"
    NESTED = "nested"
    TEST = "test"
    EXTERNAL = "external"
    UTILITY = "utility"

@dataclass(frozen=True)
class FileIdentity:
    """[Contract: Domain-Entity] Immutable identity and core metadata for a physical file."""
    path: Path
    relative_path: Path
    name: str
    extension: str
    fs_id: str  # Format: "fs:file:<relative_posix_path>"
    
    # Enhanced fields (added for Relational Bridge & Impact Analysis)
    size_bytes: int = 0
    layer: LayerType = LayerType.MODULE
    depth: int = 0

@dataclass(frozen=True)
class ImportTarget:
    """[Contract: Domain-Entity] Parsed import/call target with resolution status."""
    raw_statement: str
    resolved_path: Optional[Path]
    line_number: int
    is_resolved: bool

@dataclass
class FolderMetrics:
    """[Contract: Domain-Entity] Structural & analytical metrics for a folder."""
    depth: int = 0
    layer: LayerType = LayerType.NESTED
    file_count: int = 0
    subfolder_count: int = 0  # Replaces direct_children_count for relational clarity
    weight_score: float = 0.0
    entropy_contribution: float = 0.0
    nesting_chain: List[str] = field(default_factory=list)  # Added for AGG-01
    path_length: int = 0                                    # Added for AGG-01

@dataclass
class PhysicalNode:
    """[Contract: Graphify-Schema] Node entity strictly compatible with extraction_dict."""
    id: str
    label: str
    node_type: NodeType
    source_file: Optional[str] = None
    physical_meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PhysicalEdge:
    """[Contract: Graphify-Schema] Edge entity strictly compatible with extraction_dict."""
    source: str
    target: str
    relation: EdgeRelation
    confidence: ConfidenceLevel = ConfidenceLevel.EXTRACTED
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisContext:
    """[Contract: Pipeline-State] Shared execution context passed between domain stages."""
    root_path: Path
    ignore_patterns: List[str]
    layer_rules: Dict[str, str]
    weight_coeffs: Dict[str, float]
    max_file_size_mb: int

    # Progressive stage outputs
    folders: Dict[Path, FolderMetrics] = field(default_factory=dict)
    files: Dict[Path, FileIdentity] = field(default_factory=dict)
    imports: Dict[Path, List[ImportTarget]] = field(default_factory=dict)

    # Error & warning tracking (Fail-Soft orchestration)
    parse_errors: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Arbitrary stage-specific data (for cross-stage passing without coupling)
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StageResult:
    """[Contract: Pipeline-Orchestration] Standardized output from any pipeline stage."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

__all__ = [
    "NodeType", "EdgeRelation", "ConfidenceLevel", "LayerType",
    "FileIdentity", "ImportTarget", "FolderMetrics",
    "PhysicalNode", "PhysicalEdge", "AnalysisContext", "StageResult"
]