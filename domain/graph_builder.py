# domain/graph_builder.py
"""
Domain Stage F-05 & P-04/P-05: Graph Assembly, Impact Analysis & Cycle Detection.
Pure graph construction logic. Produces extraction_dict compatible 1:1 with Graphify.
Maps to: builders/graph_assembler.py (entirety)
"""
from __future__ import annotations
from collections import deque
from dataclasses import asdict
from typing import Dict, List, Set, Tuple, Any
from pathlib import Path

from domain.types import (
    AnalysisContext, PhysicalNode, PhysicalEdge, NodeType, EdgeRelation,
    StageResult, ConfidenceLevel, LayerType
)
from domain.classifier import generate_fs_id
from ports.stage import IPhysicalStage

# [Contract: 06-P04] BFS depth limit to prevent explosion in massive projects
MAX_REACH_DEPTH = 50

# Fallback validator until infrastructure/validator.py is fully deployed
try:
    from infrastructure.validator import validate_graphify_schema
except ImportError:
    def validate_graphify_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Minimal schema check to prevent pipeline breakage during refactoring."""
        required = {"nodes", "edges", "metadata"}
        missing = required - set(data.keys())
        if missing: return False, [f"Missing root keys: {missing}"]
        return True, []


class GraphBuilderStage(IPhysicalStage):
    """[Contract: 04-IPhysicalStage] Executes F-05, P-04, P-05 graph assembly."""

    @property
    def stage_id(self) -> str: return "domain.graph_builder"

    def execute(self, context: AnalysisContext) -> StageResult:
        """[Contract: 04-IPhysicalStage.execute] Main entry point for assembly & validation."""
        try:
            nodes = self._build_nodes(context)
            edges = self._build_edges(context)
            impact_data, cycles = self._compute_reachability_and_cycles(context, nodes, edges)
            output_dict = self._assemble_final_dict(context, nodes, edges, impact_data, cycles)
            
            # ✅ FIX: Push final output to context.data for pipeline continuity & verification
            context.data.update(output_dict)

            is_valid, validation_errors = validate_graphify_schema(output_dict)
            return StageResult(
                success=is_valid,
                data=output_dict,
                errors=validation_errors if not is_valid else []
            )
        except Exception as exc:
            context.parse_errors.append({"stage": self.stage_id, "error": str(exc), "type": type(exc).__name__})
            return StageResult(success=False, data={}, errors=[f"Assembly failed: {exc}"])

    def _build_nodes(self, context: AnalysisContext) -> List[PhysicalNode]:
        """[Contract: 08-IO-Schema-Node] Build folder & file nodes with physical metadata."""
        nodes: List[PhysicalNode] = []
        depth_map = context.data.get("depth_map", {})
        root = context.root_path.resolve()

        for folder_path, metrics in context.folders.items():
            nodes.append(PhysicalNode(
                id=generate_fs_id(folder_path, root, "folder"),
                label=folder_path.name,
                node_type=NodeType.PHYSICAL_FOLDER,
                source_file=None,
                physical_meta=asdict(metrics)
            ))

        for file_path, identity in context.files.items():
            layer = getattr(identity, "layer", LayerType.MODULE)
            layer_val = layer.value if hasattr(layer, "value") else str(layer)
            nodes.append(PhysicalNode(
                id=identity.fs_id,
                label=identity.name,
                node_type=NodeType.PHYSICAL_FILE,
                source_file=str(identity.relative_path),
                physical_meta={
                    "depth": depth_map.get(file_path.parent, 0) + 1,
                    "layer": layer_val,
                    "extension": identity.extension,
                    "size_bytes": file_path.stat().st_size if file_path.exists() else 0
                }
            ))
        return nodes

    def _build_edges(self, context: AnalysisContext) -> List[PhysicalEdge]:
        """[Contract: F-05, P-05] Structural & dependency edges."""
        edges: List[PhysicalEdge] = []
        folder_set: Set[Path] = context.data.get("folder_set", set())

        for file_path in context.files:
            parent = file_path.parent
            if parent in folder_set:
                edges.append(PhysicalEdge(
                    source=generate_fs_id(parent, context.root_path.resolve(), "folder"),
                    target=context.files[file_path].fs_id,
                    relation=EdgeRelation.CONTAINS
                ))

        siblings_map: Dict[Path, List[Path]] = {}
        for f in folder_set:
            if f.parent in folder_set:
                siblings_map.setdefault(f.parent, []).append(f)
        for children in siblings_map.values():
            for i in range(len(children)):
                for j in range(i + 1, min(i + 11, len(children))):
                    edges.append(PhysicalEdge(
                        source=generate_fs_id(children[i], context.root_path.resolve(), "folder"),
                        target=generate_fs_id(children[j], context.root_path.resolve(), "folder"),
                        relation=EdgeRelation.SIBLING
                    ))

        for src_file, imports in context.imports.items():
            src_id = context.files[src_file].fs_id
            for imp in imports:
                if imp.is_resolved and imp.resolved_path in context.files:
                    tgt_id = context.files[imp.resolved_path].fs_id
                    edges.append(PhysicalEdge(
                        source=src_id, target=tgt_id, relation=EdgeRelation.IMPORTS,
                        confidence=ConfidenceLevel.EXTRACTED,
                        meta={"line": imp.line_number, "statement": imp.raw_statement}
                    ))
        return edges

    def _compute_reachability_and_cycles(self, context: AnalysisContext, nodes: List[PhysicalNode], edges: List[PhysicalEdge]) -> Tuple[Dict[str, Any], List[List[str]]]:
        """[Contract: P-04] Reverse BFS for impact & iterative DFS for cycles."""
        adj: Dict[str, List[str]] = {}
        rev_adj: Dict[str, List[str]] = {}
        node_ids = {n.id for n in nodes}
        
        for e in edges:
            if e.relation == EdgeRelation.IMPORTS and e.source in node_ids and e.target in node_ids:
                adj.setdefault(e.source, []).append(e.target)
                rev_adj.setdefault(e.target, []).append(e.source)

        impact_scores: Dict[str, float] = {}
        entry_points: List[str] = []
        total_files = sum(1 for n in nodes if n.node_type == NodeType.PHYSICAL_FILE)

        for nid in node_ids:
            if "fs:file:" not in nid: continue
            visited: Set[str] = set()
            queue = deque([(src, 0) for src in rev_adj.get(nid, [])])
            for src, _ in queue: visited.add(src)
            while queue:
                curr, d = queue.popleft()
                if d >= MAX_REACH_DEPTH: continue
                for prev in rev_adj.get(curr, []):
                    if prev not in visited:
                        visited.add(prev)
                        queue.append((prev, d + 1))
            
            direct_impact = len(rev_adj.get(nid, []))
            transitive_impact = len(visited)
            impact_scores[nid] = transitive_impact / total_files if total_files > 0 else 0.0
            if direct_impact == 0:
                entry_points.append(nid)

        cycles: List[List[str]] = []
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {nid: WHITE for nid in node_ids}
        path_stack: List[str] = []

        for start in node_ids:
            if color[start] != WHITE: continue
            stack = [(start, iter(adj.get(start, [])))]
            color[start] = GRAY
            path_stack.append(start)
            while stack:
                u, children = stack[-1]
                try:
                    v = next(children)
                    if color[v] == GRAY:
                        idx = path_stack.index(v)
                        cycles.append(path_stack[idx:] + [v])
                    elif color[v] == WHITE:
                        color[v] = GRAY
                        path_stack.append(v)
                        stack.append((v, iter(adj.get(v, []))))
                except StopIteration:
                    color[u] = BLACK
                    path_stack.pop()
                    stack.pop()

        return {"impact_scores": impact_scores, "entry_points": entry_points}, cycles

    def _assemble_final_dict(self, context: AnalysisContext, nodes: List[PhysicalNode], edges: List[PhysicalEdge], impact: Dict, cycles: List[List[str]]) -> Dict[str, Any]:
        """[Contract: 08-IO-PrimaryOutput] Assemble final extraction_dict."""
        for n in nodes:
            if n.id in impact["impact_scores"]:
                n.physical_meta["impact_ratio"] = impact["impact_scores"][n.id]
                n.physical_meta["is_entry_point"] = n.id in impact["entry_points"]

        return {
            "nodes": [asdict(n) for n in nodes],
            "edges": [asdict(e) for e in edges],
            "metadata": {
                "analyzer": "physical_v1",
                "root_path": str(context.root_path.resolve()),
                "timestamp": context.data.get("timestamp", "")
            },
            "aggregated_metrics": {
                "entry_point_candidates": impact["entry_points"],
                "circular_dependencies": cycles,
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "parse_errors_count": len(context.parse_errors)
            }
        }

__all__ = ["GraphBuilderStage"]