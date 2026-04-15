├── __init__.py.md                      # واجهة عامة واحدة: run_physical_analysis()
├── domain/                             # 🧠 منطق المعالجة النقي (لا I/O، لا pandas/sqlalchemy)
│   ├── types.py.md                     # Dataclasses, Enums, Context, StageResult
│   ├── scanner.py.md                   # F-01: BFS/DFS traversal + ignore filtering
│   ├── metrics.py.md                   # F-02..04: Depth, Weight, Entropy
│   ├── classifier.py.md                # P-02: Semantic layer rules + fallback
│   ├── import_extractor.py.md          # P-03: Regex/tree-sitter parsing + resolution
│   └── graph_builder.py.md             # F-05, P-04, P-05: Nodes/edges, impact, cycles
├── ports/                              # 📜 طبقة التجريد الرسمية (Interfaces فقط)
│   ├── stage.py.md                     # IPhysicalStage, IPipeline
│   ├── export.py.md                    # IExportStrategy
│   ├── import_.py.md                   # IImportStrategy
│   ├── report.py.md                    # IReportGenerator
│   └── config.py.md                    # IConfigLoader
├── adapters/                           # 🔌 تنفيذ التفاعل الخارجي (يعتمد على ports فقط)
│   ├── export/                         # مُصدّرات البيانات العلائقية
│   │   ├── base.py.md                  # Registry + validation helpers
│   │   ├── csv.py.md, psql.py.md, hdf5.py.md, parquet.py.md
│   │   └── router.py.md                # Factory: get_exporter(fmt) → IExportStrategy
│   ├── import_/                        # محمّلات البيانات العلائقية
│   │   ├── base.py.md                  # Loader registry + schema detection
│   │   ├── csv.py.md, parquet.py.md, sql.py.md, hdf5.py.md
│   │   └── router.py.md                # Factory: get_loader(fmt) → IImportStrategy
│   ├── config/                         # تحميل الإعدادات
│   │   └── json_ignored.py.md          # IConfigLoader implementation
│   └── graphify/                       # تكامل مع خط أنابيب Graphify
│       ├── cli_flags.py.md             # argparse patches (--codebase-report, etc.)
│       └── pipeline_hook.py.md         # Injection into extract() → build_graph()
├── application/                        # 🔄 تنسيق سير العمل والجسور
│   ├── orchestrator.py.md              # يربط domain stages عبر ports فقط
│   ├── relational_bridge.py.md         # يوحّد forward (export) و reverse (import)
│   └── safe_merger.py.md               # دمج آمن، منع التكرار، إثراء physical_meta
├── infrastructure/                     # 🗃️ سكيما، تحقق، دوال مساعدة مشتركة
│   ├── relational_schema_v1.py.md      # تعريف الجداول، الأنواع، القيود
│   ├── graphify_schema_v1.py.md        # extraction_dict validation
│   ├── validator.py.md                 # Reference checker, type coercion, null safety
│   └── utils.py.md                     # Pure helpers (path_chain, entropy, etc.)
├── reporting/                          # 📊 توليد التقارير والـ Insights
│   ├── templates/                      # markdown.j2, html.j2, json.j2
│   ├── generator.py.md                 # IReportGenerator → Jinja2 rendering
│   └── extractor.py.md                 # Threshold evaluation, health score, traceability
└── tests/                              # 🧪 اختبارات موحدة ومقسّمة وظيفيًا
    ├── unit/                           # اختبارات كل مكون معزول
    ├── integration/                    # اختبارات تدفق كامل (Scan → Build → Export)
    └── roundtrip/                      # اختبارات عكسية (Export → Import → Merge → 1:1)