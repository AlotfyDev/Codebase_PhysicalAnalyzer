"""
Test skeleton.

Mapped by testing matrix.
Implement according to dependency order and acceptance criteria.
"""
from reporting.extractors.structure import StructureExtractor


def test_get_raw_findings_collects_folder_metrics():
    extractor = StructureExtractor()

    raw_data = {
        "nodes": [
            {
                "id": "folder:src",
                "label": "src",
                "node_type": "physical_folder",
                "physical_meta": {
                    "depth": 2,
                    "weight_score": 0.91,
                },
            },
            {
                "id": "file:src:main.py",
                "label": "main.py",
                "node_type": "physical_file",
                "physical_meta": {
                    "depth": 3,
                    "weight_score": 0.2,
                },
            },
        ],
        "aggregated_metrics": {
            "global_entropy": 0.72,
        },
    }

    findings = extractor.get_raw_findings(raw_data)

    assert findings["folder_tree_depths"] == {"folder:src": 2}
    assert findings["folder_weights"] == {"folder:src": 0.91}
    assert findings["global_entropy"] == 0.72


def test_extract_emits_depth_weight_and_entropy_insights():
    extractor = StructureExtractor()

    raw_data = {
        "nodes": [
            {
                "id": "folder:deep",
                "label": "deep",
                "node_type": "physical_folder",
                "physical_meta": {
                    "depth": 8,
                    "weight_score": 0.97,
                    "file_count": 14,
                    "subfolder_count": 0,
                },
            }
        ],
        "aggregated_metrics": {
            "global_entropy": 0.81,
        },
    }

    thresholds = {
        "max_depth": 5,
        "folder_weight_god": 0.85,
        "entropy_warn": 0.6,
        "flat_folder_files": 10,
    }

    insights = extractor.extract(raw_data, thresholds)

    categories = {i.category for i in insights}
    titles = {i.title for i in insights}

    assert len(insights) == 4

    assert "nesting_complexity" in categories
    assert "modular_violation" in categories
    assert "structural_organization" in categories
    assert "structural_chaos" in categories

    assert "Excessive Folder Nesting" in titles
    assert "Overloaded Folder (God Folder)" in titles
    assert "Flat Folder Structure" in titles
    assert "High Nesting Entropy" in titles
