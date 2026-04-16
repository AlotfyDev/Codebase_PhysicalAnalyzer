# ports/config.py
"""
[Contract: 04-Abstraction] Configuration Loader Protocol.
Pure interface. Decouples file I/O & JSON parsing from core logic.
"""
from __future__ import annotations
from pathlib import Path
from typing import Protocol, Dict, Any, List, runtime_checkable

@runtime_checkable
class IConfigLoader(Protocol):
    """
    [Contract: Strategy Pattern]
    Concrete loaders MUST implement this protocol.
    Enables environment-aware config injection (local, CI, cloud).
    """
    def load_ignore_patterns(self, root: Path) -> List[str]: ...
    def load_config(self, root: Path) -> Dict[str, Any]: ...