# Testing Matrix

This matrix maps project components to test responsibilities, dependency order, test categories, and readiness requirements.

## Columns

- `component_id`: stable identifier for the component
- `layer`: architectural layer
- `dependency_order`: lower number means earlier test dependency
- `component_path`: repository path
- `component_kind`: module, contract, adapter, scenario, or output
- `criticality`: P0, P1, or P2
- `test_category`: unit, contract, integration, e2e, regression, non_functional
- `test_target_path`: expected test file path
- `fixture_requirement`: required fixture set, if any
- `coverage_scope`: what behavior must be covered
- `acceptance_criteria`: required pass conditions
- `status`: planned, in_progress, implemented, validated
- `notes`: freeform implementation notes

## Matrix

See:
- `testing_matrix.json`
- `testing_matrix.csv`

These machine-readable files are the authoritative tracking artifacts for completeness and validation.

## Test Fixtures

Test fixtures are located in `tests/fixtures/repos/`:

| Fixture | Description | Used By Tests |
|---------|-------------|---------------|
| `clean_repo` | Minimal clean project | DOM-SCANNER, DOM-CLASSIFIER, DOM-GRAPH, APP-API, APP-ORCH, APP-RUNNER, E2E-SMOKE |
| `cycles_repo` | Circular import patterns | DOM-GRAPH, REP-DEP, E2E-CYCLES |
| `deep_repo` | 5+ level nesting | REP-STRUCT, E2E-DEEP |
| `orphan_repo` | Unreferenced files | REP-IMPACT, E2E-ORPHANS |
| `ignore_repo` | Ignore pattern scenarios | DOM-SCANNER, ADP-CONFIG, E2E-IGNORE |
| `multilang_repo` | Multiple languages | DOM-IMPORT, E2E-MULTILANG |
| `graphify_merge_repo` | Graphify integration | ADP-GRAPHIFY-HOOK, E2E-GRAPHIFY |
