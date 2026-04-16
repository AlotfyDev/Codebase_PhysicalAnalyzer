# ignore_repo - Project to test ignore patterns
# Used for: DOM-SCANNER, ADP-CONFIG, E2E-IGNORE

# Files that SHOULD be ignored
__pycache__/
*.pyc
.git/
node_modules/
venv/
.env
*.log
dist/

# Files that SHOULD be analyzed
src/
├── __init__.py
├── main.py
└── utils/
    └── helper.py