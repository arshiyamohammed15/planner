from __future__ import annotations

import os
import types
import pytest

from config.config_loader import load_config


def test_load_config_dev(monkeypatch):
    # Force env to dev
    monkeypatch.setenv("ENVIRONMENT", "dev")
    cfg = load_config()
    assert cfg["env"]["app_env"] == "development"
    assert cfg["database"]["dbname"] == "planner_dev"


def test_env_override(monkeypatch, tmp_path):
    # Create a temp config_prod.yaml to verify env-specific selection
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    prod_cfg = cfg_dir / "config_prod.yaml"
    prod_cfg.write_text(
        "env:\n  app_env: production\n  sqlalchemy_echo: ''\n"
        "database:\n  dbname: prod_db\n"
    )
    default_cfg = cfg_dir / "config.yaml"
    default_cfg.write_text("env:\n  app_env: default\n")

    monkeypatch.setenv("ENVIRONMENT", "prod")
    cfg = load_config(base_path=str(cfg_dir))
    assert cfg["env"]["app_env"] == "production"
    assert cfg["database"]["dbname"] == "prod_db"


def test_secret_merge(monkeypatch):
    # Simulate secret fetch by monkeypatching fetch_secret_optional
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("CONFIG_SECRET_NAME", "dummy")

    import config.config_loader as cl

    secrets = {"database": {"user": "secret_user"}, "api_keys": {"service1": "secret"}}
    monkeypatch.setattr(cl, "fetch_secret_optional", lambda name: secrets)

    cfg = load_config()
    # secrets should override file values where overlapping
    assert cfg["database"]["user"] == "secret_user"
    assert cfg["api_keys"]["service1"] == "secret"


