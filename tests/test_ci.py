from __future__ import annotations

import platform
import sys


def test_environment_ready():
    # Basic sanity checks for CI environment
    assert sys.version_info >= (3, 9), "Python 3.9+ required"
    assert platform.system() in {"Linux", "Windows", "Darwin"}

