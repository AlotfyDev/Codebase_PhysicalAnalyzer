# Production Testing Plan

## 1. Purpose

This document defines the production-grade testing strategy for the Physical Analyzer project.

The goal is not only to add tests, but to establish a **systematic validation program** that can measure:
- functional completeness
- architectural contract integrity
- cross-layer integration correctness
- behavioral reliability
- production readiness

The testing program is intentionally aligned with the project's dependency order and architectural boundaries.

## 2. Testing Principles

1. Tests must follow **dependency order**, from the least-dependent components to the most-dependent flows.
2. Every production-facing module must be mapped to at least one test target.
3. Every resolved bug must gain regression protection.
4. Every architectural contract must be verifiable through automated tests.
5. End-to-end coverage must be scenario-based, not only smoke-based.
6. Output validation must include schema integrity, determinism, and CI-facing behaviors.

## 3. Dependency-Ordered Test Execution Model

The test program is organized in this order:

1. Domain layer
2. Infrastructure layer
3. Ports and contract compliance
4. Adapters
5. Reporting extractors
6. Reporting aggregators and generators
7. Application layer
8. Graphify integration boundary
9. End-to-end behavioral scenarios
10. Production readiness and regression gates

This order is mandatory for systematic validation because higher layers depend on the stability of lower layers.

## 4. Test Categories

### 4.1 Unit Tests
Used for pure logic, deterministic computations, helper methods, validators, and local transformations.

### 4.2 Contract Tests
Used to verify that concrete implementations comply with declared interfaces and architectural expectations.

### 4.3 Integration Tests
Used to verify collaboration between modules, layers, and adapters.

### 4.4 End-to-End Behavioral Tests
Used to validate complete execution flows against representative repository fixtures.

### 4.5 Regression Tests
Used to prevent recurrence of previously identified runtime, merge, schema, or orchestration defects.

### 4.6 Non-Functional / Production Readiness Tests
Used for determinism, idempotency, CLI behavior, exit codes, schema stability, and repeatability.

## 5. Coverage Goals

### 5.1 Required Coverage Dimensions
The test suite must cover:
- all public entry points
- all dependency layers
- all contracts
- all critical orchestration paths
- all Graphify integration boundaries
- all known runtime regressions
- all E2E scenario classes defined in the matrix

### 5.2 Production Gate Expectations
Minimum readiness expectations:
- 100% module mapping coverage in the testing matrix
- 100% P0 component coverage
- 100% contract implementation coverage
- all E2E smoke scenarios passing
- all regression scenarios passing
- all schema validation tests passing
- deterministic repeated runs on representative fixtures

## 6. Test Structure

The test directory must use a dependency-aware structure:

```text
tests/
├── unit/
├── integration/
├── e2e/
├── contracts/
├── fixtures/
├── output/
├── conftest.py
└── pytest.ini
```

Detailed structure is provided separately in the testing filesystem package.

## 7. Fixtures Strategy

Fixture repositories must cover:
- clean small repository
- deep nesting repository
- circular dependency repository
- orphan-heavy repository
- ignore-pattern repository
- multi-language repository
- Graphify merge scenario repository

Expected outputs may be stored under `tests/fixtures/expected/` when deterministic comparisons are practical.

## 8. Output and Reporting Strategy

Test execution outputs must be collected in a dedicated output area:
- `tests/output/reports/`
- `tests/output/coverage/`
- `tests/output/logs/`
- `tests/output/artifacts/`
- `tests/output/tmp/`

These directories are intentionally versioned with `.keep` placeholders so that the structure survives compression and initial repository creation.

## 9. Tooling

Recommended tooling:
- `pytest`
- `pytest-cov`
- optional `pytest-xdist`
- optional `coverage.py`
- optional schema validation helpers

## 10. Execution Stages

### Stage A: Foundational validation
Run:
- unit/domain
- unit/infrastructure
- contracts

### Stage B: Cross-layer validation
Run:
- adapters
- reporting
- application integration

### Stage C: End-to-end validation
Run:
- e2e smoke
- e2e behavioral scenarios
- Graphify merge flow

### Stage D: Production gates
Run:
- regression suite
- deterministic rerun checks
- CLI exit-code tests
- schema stability checks

## 11. Definition of Done for Testing

Testing is considered production-ready only when:
1. all mapped components have implemented tests
2. all P0 and P1 scenarios are covered
3. all regression tests are implemented and passing
4. all required E2E scenarios pass
5. coverage and pass-rate metrics satisfy the acceptance gates
6. CI can execute the suite reproducibly

## 12. Immediate Next Steps

1. Commit the testing documents and filesystem package.
2. Add `pytest` configuration and baseline tooling.
3. Implement P0 test modules in dependency order.
4. Add fixture repositories. ✅ DONE - 7 fixture repos created
5. Wire the suite into CI.

## 13. Test Fixtures Repository

The following fixture repositories are available for E2E and integration testing:

| Fixture | Path | Purpose |
|---------|------|---------|
| **clean_repo** | `tests/fixtures/repos/clean_repo/` | Basic project, no special conditions |
| **cycles_repo** | `tests/fixtures/repos/cycles_repo/` | Circular import detection |
| **deep_repo** | `tests/fixtures/repos/deep_repo/` | Deep folder nesting (5+ levels) |
| **orphan_repo** | `tests/fixtures/repos/orphan_repo/` | Unreferenced/orphan files |
| **ignore_repo** | `tests/fixtures/repos/ignore_repo/` | Ignore pattern handling |
| **multilang_repo** | `tests/fixtures/repos/multilang_repo/` | Multi-language import extraction |
| **graphify_merge_repo** | `tests/fixtures/repos/graphify_merge_repo/` | Graphify merge flow integration |

### Fixture Requirements by Test

| Test Category | Required Fixtures |
|---------------|-------------------|
| Unit Tests | None (use mocks) |
| Integration | clean_repo, ignore_repo |
| E2E | Per test scenario (see matrix) |
| Non-Functional | clean_repo |
