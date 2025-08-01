BlockAnimator/
├── blockanimator/
│   ├── __init__.py
│   ├── __main__.py
│   │
│   ├── animation/
│   │   ├── __init__.py
│   │   ├── anim_types.py
│   │   ├── controller.py
│   │   ├── groups.py
│   │   ├── orchestrator.py
│   │   ├── proxy.py
│   │   └── timeline.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── camera.py
│   │   ├── coordinate_system.py
│   │   ├── render_manager.py
│   │   ├── renderer.py
│   │   └── scene.py
│   │
│   ├── rendering/
│   │   ├── __init__.py
│   │   ├── consensus_scene_adapter.py
│   │   └── visual_dag_renderer.py
│   │
│   ├── sprites/
│   │   ├── __init__.py
│   │   ├── block.py
│   │   └── connection.py
│   │
│   ├── consensus/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── dag_types.py
│   │   ├── manager.py
│   │   ├── visual_block.py
│   │   │
│   │   ├── blocks/
│   │   │   ├── __init__.py
│   │   │   ├── block_factory.py
│   │   │   ├── consensus_block.py
│   │   │   │
│   │   │   ├── ghostdag/
│   │   │   │   ├── __init__.py
│   │   │   │   └── ghostdag_block.py
│   │   │   │
│   │   │   └── nakamoto_consensus/
│   │   │       ├── __init__.py
│   │   │       └── bitcoin_block.py
│   │   │
│   │   └── dags/
│   │       ├── __init__.py
│   │       ├── base_dag.py
│   │       ├── consensus_dags.py
│   │       ├── dag_factory.py
│   │       ├── layer_dag.py
│   │       │
│   │       ├── ghostdag/
│   │       │   ├── __init__.py
│   │       │   └── ghostdag_dag.py
│   │       │
│   │       └── nakamoto_consensus/
│   │           ├── __init__.py
│   │           └── bitcoin_dag.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── module_ops.py
│
└── examples/
    └── demo_scenes.py