from application.orchestrator import run_analysis

# 1. الاستخدام الأساسي
graphify_dict = run_analysis("./my_project")

# 2. مع تجاوزات ديناميكية
graphify_dict = run_analysis(
    "./my_project",
    config_overrides={
        "layer_rules": {"**/api/**": "core", "**/tests/**": "test"},
        "weight_coeffs": {"density": 0.6, "depth_penalty": 0.2, "centrality": 0.2},
        "max_file_size_mb": 10
    }
)

# 3. التكامل مع Graphify
extractions["nodes"].extend(graphify_dict["nodes"])
extractions["edges"].extend(graphify_dict["edges"])
extractions["metadata"]["physical_analysis"] = graphify_dict["metadata"]