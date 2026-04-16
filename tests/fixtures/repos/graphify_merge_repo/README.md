# graphify_merge_repo - Project for testing Graphify merge flow
# Used for: ADP-GRAPHIFY-HOOK, E2E-GRAPHIFY

# This fixture tests the integration between Physical Analyzer
# and Graphify's extraction pipeline.

# Physical Analyzer outputs (simulated Graphify input)
physical_output/
├── nodes.json
├── edges.json
└── metadata.json

# Graphify-compatible structure
src/
├── __init__.py
├── main.py
└── models/
    ├── __init__.py
    └── user.py

# Test expects:
# 1. Physical nodes/edges to merge correctly with Graphify output
# 2. No duplicate node IDs
# 3. metadata.physical_analysis to be injected