# adapters/graphify/cli_flags.py
"""
CLI Argument Extensions: Registers Physical Analyzer flags into Graphify's ArgumentParser.
Designed for clean injection without modifying Graphify's core argument logic.
"""
from __future__ import annotations
import argparse


def add_cli_flags(parser: argparse.ArgumentParser) -> None:
    """
    [Contract: 08-IO-CLI]
    Adds a dedicated argument group for Physical Analyzer features.
    Compatible with Graphify's existing __main__.py setup.
    """
    group = parser.add_argument_group("physical analysis & insights")
    group.add_argument(
        "--codebase-report", action="store_true",
        help="Enable deep physical filesystem analysis & architectural insights"
    )
    group.add_argument(
        "--report-format", type=str, choices=["json", "markdown", "html"], default="markdown",
        help="Output format for architectural insights report (default: markdown)"
    )
    group.add_argument(
        "--relational-export", type=str, choices=["csv", "postgresql", "hdf5", "parquet"], default=None,
        help="Export relational aggregation tables to specified format"
    )
    group.add_argument(
        "--output", type=str, default="graphify-out",
        help="Output directory for reports, exports, and cache (default: graphify-out)"
    )


__all__ = ["add_cli_flags"]