"""Tests for the framework-agnostic disclaimer core.

These tests do NOT require Streamlit, Flask, or PySide6. They exercise:

1. Hash stability and change detection.
2. Marker-file persistence (accept → marker → re-check).
3. Re-acknowledgement after disclaimer-text change (hash mismatch).
4. Re-acknowledgement after version bump.
5. Label completeness (4 mandatory labels, DE + EN).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make _data importable.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _REPO_ROOT / "_data"
sys.path.insert(0, str(_DATA_DIR))

import disclaimer_core as dc  # noqa: E402


def test_four_mandatory_labels_bilingual():
    assert len(dc.ACKNOWLEDGEMENT_LABELS_DE) == 4
    assert len(dc.ACKNOWLEDGEMENT_LABELS_EN) == 4
    joined_de = " ".join(dc.ACKNOWLEDGEMENT_LABELS_DE)
    # Core legal terms must appear in the DE labels
    for needle in (
        "Medizinprodukt",
        "Diagnose",
        "ärztliche",
        "EIGENES RISIKO",
    ):
        assert needle in joined_de, f"missing in DE labels: {needle}"
    joined_en = " ".join(dc.ACKNOWLEDGEMENT_LABELS_EN)
    for needle in ("medical device", "diagnosis", "OWN RISK"):
        assert needle in joined_en, f"missing in EN labels: {needle}"


def test_hash_is_stable_and_changes_with_text():
    h1 = dc.compute_disclaimer_hash("hello world")
    h2 = dc.compute_disclaimer_hash("hello world")
    h3 = dc.compute_disclaimer_hash("hello world ")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # sha256 hex


def test_accept_and_verify_roundtrip(tmp_path: Path):
    marker = tmp_path / "disclaimer_accepted.json"
    # Start state: not accepted
    assert dc.is_accepted(path=marker) is False

    # Record acceptance with a known text
    dc.record_acceptance(text="DUMMY TEXT", path=marker)
    assert marker.is_file()

    # Current NOTICE text hash != DUMMY TEXT hash, so is_accepted(with default
    # hash) must be False; but when we pass the known hash we get True.
    dummy_hash = dc.compute_disclaimer_hash("DUMMY TEXT")
    assert dc.is_accepted(current_hash=dummy_hash, path=marker) is True


def test_hash_mismatch_forces_reacceptance(tmp_path: Path):
    marker = tmp_path / "disclaimer_accepted.json"
    dc.record_acceptance(text="OLD TEXT", path=marker)
    # Simulate text change: new hash does not match stored hash
    new_hash = dc.compute_disclaimer_hash("NEW TEXT")
    assert dc.is_accepted(current_hash=new_hash, path=marker) is False


def test_version_bump_invalidates_acceptance(tmp_path: Path, monkeypatch):
    marker = tmp_path / "disclaimer_accepted.json"
    dc.record_acceptance(text="STABLE TEXT", path=marker)
    stable_hash = dc.compute_disclaimer_hash("STABLE TEXT")

    # Same text/hash → still accepted
    assert dc.is_accepted(current_hash=stable_hash, path=marker) is True

    # Bump the DISCLAIMER_VERSION → must invalidate
    monkeypatch.setattr(dc, "DISCLAIMER_VERSION", "2.0")
    assert dc.is_accepted(current_hash=stable_hash, path=marker) is False


def test_marker_file_schema(tmp_path: Path):
    marker = tmp_path / "disclaimer_accepted.json"
    dc.record_acceptance(
        text="ANY",
        acknowledged_labels=["a", "b", "c", "d"],
        path=marker,
    )
    data = json.loads(marker.read_text(encoding="utf-8"))
    for key in (
        "event",
        "disclaimer_version",
        "disclaimer_hash",
        "accepted_at",
        "acknowledged_labels",
    ):
        assert key in data, f"missing key in marker: {key}"
    assert data["event"] == "first_start_acknowledgement"
    assert data["acknowledged_labels"] == ["a", "b", "c", "d"]


def test_notice_file_is_loaded_when_present():
    # The repo-level NOTICE must exist and be loaded as disclaimer text.
    text = dc.load_disclaimer_text()
    assert isinstance(text, str) and text
    # The NOTICE file contains these sentinels (DE + EN).
    assert "Medizinprodukt" in text or "medical device" in text.lower()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
