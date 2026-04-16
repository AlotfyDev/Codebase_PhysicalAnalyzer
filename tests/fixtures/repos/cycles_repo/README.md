# cycles_repo - Project with circular dependencies
# Used for: DOM-GRAPH, REP-DEP, E2E-CYCLES

src/
├── __init__.py
├── a.py          # imports b
├── b.py          # imports c
├── c.py          # imports a (creates cycle)
└── utils/
    └── helper.py  # clean, no cycles