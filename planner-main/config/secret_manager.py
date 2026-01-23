from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover - optional dependency
    boto3 = None
    BotoCoreError = ClientError = Exception


class SecretManager:
    """
    Simple wrapper to fetch secrets from AWS Secrets Manager.
    """

    def __init__(self, region_name: Optional[str] = None):
        self.region = region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        if boto3 is None:
            raise ImportError("boto3 is required for SecretManager. Install boto3 to use this feature.")
        self.client = boto3.client("secretsmanager", region_name=self.region)

    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve and parse a JSON secret by name/ARN.
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover - network call
            raise RuntimeError(f"Failed to fetch secret {secret_name}: {exc}") from exc

        if "SecretString" in response:
            return json.loads(response["SecretString"])
        elif "SecretBinary" in response:
            return json.loads(response["SecretBinary"])
        raise RuntimeError(f"Secret {secret_name} contained no SecretString or SecretBinary")


def fetch_secret_optional(secret_name: Optional[str]) -> Dict[str, Any]:
    """
    Best-effort secret fetch. Returns {} if no name provided or boto3 missing.
    """
    if not secret_name:
        return {}
    if boto3 is None:
        return {}
    return SecretManager().get_secret(secret_name)


__all__ = ["SecretManager"]

