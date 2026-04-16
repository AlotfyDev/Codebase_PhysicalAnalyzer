# adapters/config/json_ignored.py
"""
[Contract: 08-IO] Implements ports.config.IConfigLoader.
Handles .graphifyignore & graphify-physical.json with safe defaults & fallbacks.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from ports.config import IConfigLoader

# Default constants (moved from legacy constants.py for encapsulation)
DEFAULT_IGNORE_PATTERNS = [".git", "__pycache__", "node_modules", ".venv", "dist", "build"]
DEFAULT_LAYER_RULES = {"**/test*": "test", "**/src/**": "core", "**/utils/**": "utility"}
DEFAULT_WEIGHT_COEFFS = {"density": 0.5, "depth_penalty": 0.3, "centrality": 0.2}
DEFAULT_MAX_FILE_SIZE_MB = 5

logger = logging.getLogger(__name__)

class JsonConfigLoader(IConfigLoader):
    """Production-ready config loader implementing IConfigLoader."""
    
    def load_ignore_patterns(self, root: Path) -> List[str]:
        ignore_file = root / ".graphifyignore"
        if not ignore_file.exists():
            return list(DEFAULT_IGNORE_PATTERNS)
        
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            return patterns if patterns else list(DEFAULT_IGNORE_PATTERNS)
        except Exception as e:
            logger.warning("Failed to load .graphifyignore, using defaults: %s", e)
            return list(DEFAULT_IGNORE_PATTERNS)

    def load_config(self, root: Path) -> Dict[str, Any]:
        config_file = root / "graphify-physical.json"
        defaults = {
            "layer_rules": dict(DEFAULT_LAYER_RULES),
            "weight_coeffs": dict(DEFAULT_WEIGHT_COEFFS),
            "max_file_size_mb": DEFAULT_MAX_FILE_SIZE_MB
        }
        
        if not config_file.exists():
            return defaults
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            
            if "layer_rules" in user_cfg: defaults["layer_rules"].update(user_cfg["layer_rules"])
            if "weight_coeffs" in user_cfg: defaults["weight_coeffs"].update(user_cfg["weight_coeffs"])
            if "max_file_size_mb" in user_cfg: defaults["max_file_size_mb"] = user_cfg["max_file_size_mb"]
        except (json.JSONDecodeError, IOError, TypeError) as e:
            logger.warning("Failed to parse graphify-physical.json, using defaults: %s", e)
            
        return defaults