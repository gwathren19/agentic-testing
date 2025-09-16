import tomllib
from pathlib import Path
from types import SimpleNamespace
from functools import lru_cache


def _dict_to_namespace(d: dict):
    return SimpleNamespace(
        **{k: _dict_to_namespace(v) if isinstance(v, dict) else v for k, v in d.items()}
    )


@lru_cache
def load_config():
    project_root = Path(__file__).resolve().parents[3]
    config_path = project_root / "config.toml"

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    return _dict_to_namespace(raw)


config = load_config()
