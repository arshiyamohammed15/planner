from __future__ import annotations

import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ensure PostgreSQL environment variables are set if not already present
# This helps when the API is started without the PowerShell script or if env vars aren't inherited
if not os.environ.get("POSTGRES_PASSWORD"):
    # Try to set from common locations or use defaults
    # Check if we're in a development environment
    if os.path.exists("start_api.ps1"):
        # If start_api.ps1 exists, we're in the project directory
        # Set default values that match start_api.ps1
        if not os.environ.get("POSTGRES_USER"):
            os.environ["POSTGRES_USER"] = "postgres"
        if not os.environ.get("POSTGRES_PASSWORD"):
            os.environ["POSTGRES_PASSWORD"] = "Arshiya@10"  # Default from start_api.ps1
        if not os.environ.get("POSTGRES_HOST"):
            os.environ["POSTGRES_HOST"] = "localhost"
        if not os.environ.get("POSTGRES_PORT"):
            os.environ["POSTGRES_PORT"] = "5432"
        if not os.environ.get("POSTGRES_DB"):
            os.environ["POSTGRES_DB"] = "mydatabase"

# Declarative base for ORM models
Base = declarative_base()


def build_postgres_url(
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
    database: Optional[str] = None,
    ssl_mode: Optional[str] = None,
) -> str:
    """
    Build a PostgreSQL connection URL from explicit params or environment variables.

    Env vars used (fallback order):
      POSTGRES_USER
      POSTGRES_PASSWORD
      POSTGRES_HOST (default: localhost)
      POSTGRES_PORT (default: 5432)
      POSTGRES_DB   (default: planner)
      POSTGRES_SSL_MODE (optional, e.g., require)
    """
    # #region agent log
    import json
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"postgresql_setup.py:build_postgres_url","message":"Building PostgreSQL URL - checking env vars","data":{"POSTGRES_USER":os.environ.get("POSTGRES_USER","NOT_SET"),"POSTGRES_PASSWORD_SET":bool(os.environ.get("POSTGRES_PASSWORD")),"POSTGRES_HOST":os.environ.get("POSTGRES_HOST","NOT_SET"),"POSTGRES_PORT":os.environ.get("POSTGRES_PORT","NOT_SET"),"POSTGRES_DB":os.environ.get("POSTGRES_DB","NOT_SET")},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    user = user or os.environ.get("POSTGRES_USER", "postgres")
    password = password or os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = host or os.environ.get("POSTGRES_HOST", "localhost")
    port = port or os.environ.get("POSTGRES_PORT", "5432")
    database = database or os.environ.get("POSTGRES_DB", "planner")
    ssl_mode = ssl_mode or os.environ.get("POSTGRES_SSL_MODE")

    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"postgresql_setup.py:build_postgres_url","message":"Env vars read - before encoding","data":{"user":user,"password_length":len(password) if password else 0,"password_starts_with":password[:2] if password else None,"host":host,"port":port,"database":database},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion

    # URL-encode password to handle special characters like @, :, /, etc.
    # But check if password is already URL-encoded (contains %XX patterns)
    from urllib.parse import quote_plus
    import re
    
    if password:
        # Check if password looks like it's already URL-encoded (contains %XX patterns)
        # If it does, use it as-is. Otherwise, encode it.
        is_already_encoded = bool(re.search(r'%[0-9A-Fa-f]{2}', password))
        if is_already_encoded:
            # Password appears to be already encoded, use as-is
            encoded_password = password
        else:
            # Password is not encoded, encode it
            encoded_password = quote_plus(password)
        
        # #region agent log
        try:
            with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"postgresql_setup.py:build_postgres_url","message":"Password encoding decision","data":{"password_length":len(password),"is_already_encoded":is_already_encoded,"encoded_length":len(encoded_password),"password_preview":password[:3] + "..." if len(password) > 3 else password},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
        except: pass
        # #endregion
        
        auth_part = f"{user}:{encoded_password}@"
    else:
        auth_part = f"{user}@"
    params = f"?sslmode={ssl_mode}" if ssl_mode else ""
    url = f"postgresql+psycopg2://{auth_part}{host}:{port}/{database}{params}"
    
    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"postgresql_setup.py:build_postgres_url","message":"PostgreSQL URL built","data":{"url_without_password":url.split("@")[0] + "@" + url.split("@")[1].split("/")[0] if "@" in url else "N/A","host":host,"port":port,"database":database,"password_encoded":bool(encoded_password) if password else False},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    return url


def get_engine(url: Optional[str] = None) -> Engine:
    """
    Create a SQLAlchemy engine for PostgreSQL.

    Env vars:
      DATABASE_URL (takes precedence if set)
      APP_ENV (if 'test', sets echo=False regardless of env)
      SQLALCHEMY_ECHO (truthy to enable SQL echo)
    """
    # #region agent log
    import json
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"postgresql_setup.py:get_engine","message":"Creating engine - checking URL source","data":{"has_url_param":bool(url),"has_DATABASE_URL":bool(os.environ.get("DATABASE_URL")),"will_build_url":not url and not os.environ.get("DATABASE_URL")},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    db_url = url or os.environ.get("DATABASE_URL") or build_postgres_url()
    
    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            url_display = db_url.split("@")[0] + "@" + db_url.split("@")[1].split("/")[0] if "@" in db_url else db_url[:50]
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"postgresql_setup.py:get_engine","message":"Engine URL determined","data":{"url_preview":url_display,"host_in_url":db_url.split("@")[1].split(":")[0] if "@" in db_url else "N/A","port_in_url":db_url.split(":")[-1].split("/")[0] if ":" in db_url else "N/A"},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    app_env = os.environ.get("APP_ENV", "").lower()
    echo_env = os.environ.get("SQLALCHEMY_ECHO", "").lower()
    echo = False if app_env == "test" else echo_env in {"1", "true", "yes", "on"}

    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"postgresql_setup.py:get_engine","message":"About to create engine","data":{"pool_pre_ping":True,"echo":echo},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        future=True,
        echo=echo,
    )
    
    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"postgresql_setup.py:get_engine","message":"Engine object created (connection will be tested on first use)","data":{"engine_url_preview":str(engine.url).split("@")[0] + "@" + str(engine.url).split("@")[1].split("/")[0] if "@" in str(engine.url) else str(engine.url)[:50]},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    return engine


def get_sessionmaker(engine: Optional[Engine] = None) -> sessionmaker:
    # #region agent log
    import json
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"postgresql_setup.py:get_sessionmaker","message":"get_sessionmaker called","data":{"has_engine_param":bool(engine)},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    try:
        engine = engine or get_engine()
    except Exception as e:
        # #region agent log
        try:
            with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                error_str = str(e)
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"postgresql_setup.py:get_sessionmaker","message":"get_engine() failed","data":{"error_type":type(e).__name__,"error":error_str[:400],"has_password_auth":'password authentication' in error_str.lower(),"has_ipv6":'::1' in error_str},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
        except: pass
        # #endregion
        raise
    
    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"postgresql_setup.py:get_sessionmaker","message":"Engine obtained, creating sessionmaker","data":{},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_session(engine: Optional[Engine] = None) -> Generator:
    """
    Yield a database session, ensuring proper close/rollback.
    Suitable for FastAPI dependency usage.
    """
    SessionLocal = get_sessionmaker(engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


__all__ = [
    "Base",
    "build_postgres_url",
    "get_engine",
    "get_sessionmaker",
    "get_session",
]

