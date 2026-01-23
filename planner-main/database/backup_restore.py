from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from typing import Iterable, List, Optional, Sequence

from sqlalchemy.engine import make_url, URL

from database.postgresql_setup import build_postgres_url


def _get_url(db_url: Optional[str] = None) -> URL:
    raw = db_url or os.environ.get("DATABASE_URL") or build_postgres_url()
    return make_url(raw)


def _pg_auth_env(url: URL) -> dict:
    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password
    return env


def _conn_args(url: URL) -> List[str]:
    return [
        f"--host={url.host or 'localhost'}",
        f"--port={url.port or 5432}",
        f"--username={url.username or 'postgres'}",
        url.database or "postgres",
    ]


def backup_database(
    output_path: str,
    db_url: Optional[str] = None,
    fmt: str = "plain",
    extra_args: Optional[Iterable[str]] = None,
) -> subprocess.CompletedProcess:
    """
    Create a PostgreSQL backup using pg_dump.

    fmt: "plain" (default) or "custom". For cloud-hosted DBs, ensure pg_dump can reach the host.
    """
    if not shutil.which("pg_dump"):
        raise RuntimeError("pg_dump not found on PATH. Install PostgreSQL client tools.")

    url = _get_url(db_url)
    env = _pg_auth_env(url)
    fmt_flag = "-F" if fmt != "plain" else None
    fmt_val = "c" if fmt == "custom" else "p"

    cmd: List[str] = ["pg_dump"]
    if fmt_flag:
        cmd.extend([fmt_flag, fmt_val])
    cmd.extend(_conn_args(url))
    cmd.extend(["-f", output_path])
    if extra_args:
        cmd.extend(list(extra_args))

    return subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)


def restore_database(
    input_path: str,
    db_url: Optional[str] = None,
    fmt: str = "plain",
    extra_args: Optional[Iterable[str]] = None,
    drop_existing: bool = False,
) -> subprocess.CompletedProcess:
    """
    Restore a PostgreSQL backup.

    fmt: "plain" expects a SQL dump (uses psql).
         "custom" expects a custom-format dump (uses pg_restore).
    drop_existing: if True and fmt="custom", adds --clean to pg_restore.
    """
    url = _get_url(db_url)
    env = _pg_auth_env(url)

    if fmt == "custom":
        if not shutil.which("pg_restore"):
            raise RuntimeError("pg_restore not found on PATH. Install PostgreSQL client tools.")
        cmd: List[str] = ["pg_restore"]
        if drop_existing:
            cmd.append("--clean")
        conn = _conn_args(url)
        # pg_restore expects db name separately, already included in conn args
        cmd.extend(conn)
        if extra_args:
            cmd.extend(list(extra_args))
        cmd.append(input_path)
    else:
        if not shutil.which("psql"):
            raise RuntimeError("psql not found on PATH. Install PostgreSQL client tools.")
        cmd = ["psql"]
        conn = _conn_args(url)
        cmd.extend(conn)
        cmd.extend(["-f", input_path])
        if extra_args:
            cmd.extend(list(extra_args))

    return subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)


__all__ = ["backup_database", "restore_database"]

