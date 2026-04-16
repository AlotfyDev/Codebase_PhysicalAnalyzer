from types import SimpleNamespace

from adapters.graphify import pipeline_hook


def test_inject_physical_analysis_returns_existing_when_disabled():
    args = SimpleNamespace(codebase_report=False, output="graphify-out")
    existing = {"nodes": [{"id": "n1"}], "edges": [], "metadata": {"source": "graphify"}}

    result = pipeline_hook.inject_physical_analysis("/tmp/project", args, existing)

    assert result == existing


def test_inject_physical_analysis_merges_metadata_and_preserves_existing(monkeypatch, tmp_path):
    args = SimpleNamespace(codebase_report=True, output=str(tmp_path / "out"))
    existing = {
        "nodes": [{"id": "existing-node", "label": "Existing", "node_type": "semantic"}],
        "edges": [],
        "metadata": {"source": "graphify"},
    }

    physical_result = {
        "success": True,
        "data": {
            "nodes": [
                {
                    "id": "fs:file:src:main.py",
                    "label": "main.py",
                    "node_type": "physical_file",
                    "source_file": "src/main.py",
                    "physical_meta": {"depth": 2, "impact_ratio": 0.2},
                }
            ],
            "edges": [
                {
                    "source": "existing-node",
                    "target": "fs:file:src:main.py",
                    "relation": "contains",
                }
            ],
            "metadata": {"timestamp": "2026-04-16T12:00:00Z", "root_path": "/tmp/project"},
        },
        "errors": [],
        "warnings": ["demo warning"],
    }

    monkeypatch.setattr(pipeline_hook, "run_analysis_safe", lambda root_path, config_overrides=None: physical_result)

    merged = pipeline_hook.inject_physical_analysis("/tmp/project", args, existing)

    assert "physical_analysis" in merged["metadata"]
    assert "physical_report" in merged["metadata"]
    assert merged["metadata"]["physical_report"]["success"] is True
    assert merged["metadata"]["physical_report"]["warnings"] == ["demo warning"]
    assert any(node["id"] == "existing-node" for node in merged["nodes"])
    assert any(node["id"] == "fs:file:src:main.py" for node in merged["nodes"])


def test_inject_physical_analysis_is_fail_soft_on_analysis_failure(monkeypatch, tmp_path):
    args = SimpleNamespace(codebase_report=True, output=str(tmp_path / "out"))

    failed_result = {
        "success": False,
        "data": {"nodes": [], "edges": [], "metadata": {}},
        "errors": ["analysis failed"],
        "warnings": [],
    }

    monkeypatch.setattr(pipeline_hook, "run_analysis_safe", lambda root_path, config_overrides=None: failed_result)

    merged = pipeline_hook.inject_physical_analysis("/tmp/project", args, {"nodes": [], "edges": [], "metadata": {}})

    assert merged["metadata"]["physical_report"]["success"] is False
    assert merged["metadata"]["physical_report"]["errors"] == ["analysis failed"]
    assert merged["nodes"] == []
    assert merged["edges"] == []
