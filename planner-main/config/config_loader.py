from __future__ import annotations

import os
import re
from typing import Any, Mapping, Optional

import yaml

from config.secret_manager import fetch_secret_optional


_env_pattern = re.compile(r"\$\{([^}:]+)(?::-(.*))?}")


def _expand_env(value: Any) -> Any:
    """
    Expand ${VAR} or ${VAR:-default} in strings. Leaves other types unchanged.
    """
    if not isinstance(value, str):
        return value

    def replace(match: re.Match) -> str:
        var, default = match.group(1), match.group(2)
        return os.environ.get(var, default or "")

    return _env_pattern.sub(replace, value)


def _expand_mapping(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _expand_mapping(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_mapping(v) for v in obj]
    return _expand_env(obj)


def load_config(
    env: Optional[str] = None,
    base_path: str = "config",
    default_file: str = "config.yaml",
    secret_name: Optional[str] = None,
) -> Mapping[str, Any]:
    """
    Load configuration with optional environment-specific override.
    - If env is provided (or ENVIRONMENT/APP_ENV), looks for config_<env>.yaml in base_path.
    - Falls back to default_file if env-specific file is missing.
    - If secret_name (or CONFIG_SECRET_NAME env var) is set, merges secrets into config (overrides file values).
    """
    env = env or os.getenv("ENVIRONMENT") or os.getenv("APP_ENV")
    secret_name = secret_name or os.getenv("CONFIG_SECRET_NAME")
    files_to_try = []
    if env:
        files_to_try.append(os.path.join(base_path, f"config_{env}.yaml"))
    files_to_try.append(os.path.join(base_path, default_file))

    for path in files_to_try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            expanded = _expand_mapping(data)
            secrets = fetch_secret_optional(secret_name)
            if secrets:
                # shallow merge; secrets override file values where keys overlap
                merged = {**expanded, **secrets}
            else:
                merged = expanded
            return merged

    raise FileNotFoundError(f"No config file found in {files_to_try}")


__all__ = ["load_config"]

