"""Shared test setup for backend tests.

Keeps ChromaDB writes hermetic (temp dir instead of ./chroma_db in the repo)
and disables its outbound telemetry during tests.
"""

import os
import tempfile

os.environ.setdefault("CHROMA_PATH", tempfile.mkdtemp(prefix="r2b-chroma-test-"))
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
