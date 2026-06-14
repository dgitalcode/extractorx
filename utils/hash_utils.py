"""
D-GITALCODE ExtractorX - Hashing utilities.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

MD5/SHA-256 hashing helpers used for duplicate image detection.
"""

from __future__ import annotations

import hashlib
from typing import Set


def compute_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Return the hex digest of ``data`` using ``algorithm`` (sha256 or md5)."""
    if algorithm not in ("sha256", "md5"):
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    return hashlib.new(algorithm, data).hexdigest()


class DuplicateDetector:
    """Track image hashes to detect duplicates across one or many documents."""

    def __init__(self, algorithm: str = "sha256") -> None:
        self._algorithm = algorithm
        self._seen: Set[str] = set()

    def register(self, data: bytes) -> tuple[str, bool]:
        """Hash ``data`` and register it.

        Returns:
            Tuple of (hex digest, is_duplicate). The first occurrence of a
            payload is registered and reported as not duplicate.
        """
        digest = compute_hash(data, self._algorithm)
        if digest in self._seen:
            return digest, True
        self._seen.add(digest)
        return digest, False

    @property
    def unique_count(self) -> int:
        """Number of distinct payloads registered so far."""
        return len(self._seen)

    def reset(self) -> None:
        """Forget all registered hashes."""
        self._seen.clear()
