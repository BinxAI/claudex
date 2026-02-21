"""Per-stack LAYER_CONFIG and SIBLING_BLOCKS presets.

Used by patch_layer_config() in copier.py to write enforced architecture
rules into pre-tool-use.py at `claudex init` time.

Each preset targets the most common directory layout for that stack.
Users can edit pre-tool-use.py after init to adjust paths.
"""

from __future__ import annotations

# Each entry: {"layer_config": dict, "sibling_blocks": dict}
# Values are rendered as Python repr() into pre-tool-use.py.

PRESETS: dict[str, dict] = {
    "python-fastapi": {
        "layer_config": {
            "src/core/": ["sqlalchemy", "fastapi", "redis", "httpx", "requests", "aiohttp"],
            "src/db/": [],
            "src/api/": [],
            "src/worker/": [],
        },
        "sibling_blocks": {
            "src/core/": ["from src.db", "from src.api", "from src.worker"],
            "src/db/": ["from src.api", "from src.worker"],
            "src/worker/": ["from src.api"],
        },
        "layer_file_blocks": {
            "src/core/": ["llm", "openai", "anthropic", "client"],
        },
    },
    "python-django": {
        "layer_config": {
            "apps/": [],
        },
        "sibling_blocks": {},
        "layer_file_blocks": {},
    },
    "nextjs": {
        "layer_config": {
            "src/lib/": ["react", "@/components"],
            "src/components/": ["next/server"],
        },
        "sibling_blocks": {},
        "layer_file_blocks": {},
    },
    "generic": {
        "layer_config": {},
        "sibling_blocks": {},
        "layer_file_blocks": {},
    },
}


def get_preset(preset_name: str) -> dict:
    """Return the layer config preset for a given preset name.

    Falls back to 'generic' for unknown presets.
    """
    return PRESETS.get(preset_name, PRESETS["generic"])
