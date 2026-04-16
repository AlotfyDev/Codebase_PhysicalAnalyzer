"""
Test skeleton.

Mapped by testing matrix.
Implement according to dependency order and acceptance criteria.
"""

from reporting.extractors.impact import ImpactExtractor


def test_get_raw_findings_builds_inbound_map():
    extractor = ImpactExtractor()

    raw_data = {
        "edges": [
            {"relation": "imports", "target": "file:a"},
            {"relation": "imports", "target": "file:a"},
            {"relation": "imports", "target": "file:b"},
        ]
    }

    findings = extractor.get_raw_findings(raw_data)

    assert findings["inbound_dependency_map"] == {
        "file:a": 2,
        "file:b": 1,
    }


def test_extract_detects_hotspots_godfiles_and_orphans():
    extractor = ImpactExtractor()

    raw_data = {
        "nodes": [
            {
                "id": "file:hot",
                "node_type": "physical_file",
                "physical_meta": {"impact_ratio": 0.2, "layer": "core"},
            },
            {
                "id": "file:god",
                "node_type": "physical_file",
                "physical_meta": {"impact_ratio": 0.05, "layer": "core"},
            },
            {
                "id": "file:orphan",
                "node_type": "physical_file",
                "physical_meta": {"impact_ratio": 0.01, "layer": "core"},
            },
        ],
        "edges": [
            {"relation": "imports", "target": "file:god"} for _ in range(25)
        ],
    }

    thresholds = {
        "impact_hotspot": 0.15,
        "god_file_impact": 20,
        "orphan_files_allowed": 0,
    }

    insights = extractor.extract(raw_data, thresholds)

    categories = {i.category for i in insights}

    assert "impact_concentration" in categories
    assert "centralization_risk" in categories
    assert "dead_code_risk" in categories
