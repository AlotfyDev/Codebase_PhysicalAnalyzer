from types import SimpleNamespace

import pytest

from application import orchestrator as orch_module


class DummyStage:
    def __init__(self, stage_id, success=True, errors=None, warnings=None):
        self.stage_id = stage_id
        self._success = success
        self._errors = errors or []
        self._warnings = warnings or []

    def execute(self, ctx):
        return SimpleNamespace(
            success=self._success,
            data={},
            errors=self._errors,
            warnings=self._warnings,
        )


class DummyContext:
    def __init__(self):
        self.data = {}
        self.parse_errors = []


class DummyStageResult:
    def __init__(self, success, data=None, errors=None, warnings=None):
        self.success = success
        self.data = data or {}
        self.errors = errors or []
        self.warnings = warnings or []


def test_orchestrator_executes_all_stages_in_order(monkeypatch):
    order = []

    class OrderedStage(DummyStage):
        def execute(self, ctx):
            order.append(self.stage_id)
            return super().execute(ctx)

    stages = [OrderedStage("s1"), OrderedStage("s2"), OrderedStage("s3")]

    monkeypatch.setattr(orch_module, "AnalysisContext", lambda **kwargs: DummyContext())
    monkeypatch.setattr(orch_module, "StageResult", DummyStageResult)

    orch = orch_module.PhysicalAnalyzerOrchestrator(root_path=".")
    orch._stages = stages

    result = orch.execute()

    assert result.success is True
    assert order == ["s1", "s2", "s3"]


def test_orchestrator_fail_fast_on_stage_failure(monkeypatch):
    stages = [DummyStage("s1"), DummyStage("s2", success=False)]

    monkeypatch.setattr(orch_module, "AnalysisContext", lambda **kwargs: DummyContext())
    monkeypatch.setattr(orch_module, "StageResult", DummyStageResult)

    orch = orch_module.PhysicalAnalyzerOrchestrator(root_path=".")
    orch._stages = stages

    result = orch.execute()

    assert result.success is False
    assert any("FAIL-FAST" in err for err in result.errors)


def test_orchestrator_collects_errors_and_warnings(monkeypatch):
    stages = [
        DummyStage("s1", errors=["e1"], warnings=["w1"]),
        DummyStage("s2", errors=["e2"], warnings=["w2"]),
    ]

    ctx = DummyContext()
    ctx.parse_errors = [{"error": "parse-error"}]

    monkeypatch.setattr(orch_module, "AnalysisContext", lambda **kwargs: ctx)
    monkeypatch.setattr(orch_module, "StageResult", DummyStageResult)

    orch = orch_module.PhysicalAnalyzerOrchestrator(root_path=".")
    orch._stages = stages

    result = orch.execute()

    assert result.success is True
    assert "parse-error" in result.errors
    assert "e1" in result.errors
    assert "e2" in result.errors
    assert "w1" in result.warnings
    assert "w2" in result.warnings
