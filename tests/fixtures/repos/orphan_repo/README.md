# orphan_repo - Project with orphaned/unreferenced files
# Used for: REP-IMPACT, E2E-ORPHANS

src/
├── __init__.py
├── main.py       # entry point - referenced
├── module_a.py   # imported by main
├── module_b.py   # imported by main
└── orphan.py     # NOT imported anywhere - orphan!
legacy/
├── old_util.py   # NOT imported anywhere - orphan!
└── deprecated.py # NOT imported anywhere - orphan!