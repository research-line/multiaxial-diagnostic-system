"""First-start acknowledgement — framework-agnostic core.

Provides the disclaimer text, a SHA-256 hash of that text, persistence
helpers, and the four mandatory acknowledgement labels (DE + EN).

This module has **no dependency** on Streamlit, Flask, or PySide6 and
can be imported in headless tests.

Persistence: a JSON marker file below a user-level config directory.
Re-acknowledgement is required when the disclaimer text changes (hash
mismatch) or when the DISCLAIMER_VERSION is bumped.

Design note: We deliberately hash the **NOTICE** file content. If the
NOTICE file is updated (e.g. new version of the legal notice), the
stored hash will no longer match and the user is asked to acknowledge
the new text on the next start.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DISCLAIMER_VERSION = "1.0"
ACK_MARKER_FILENAME = "disclaimer_accepted.json"

_MODULE_DIR = Path(__file__).resolve().parent
_REPO_ROOT_CANDIDATES = [
    _MODULE_DIR.parent,        # _data/ -> repo root
    _MODULE_DIR.parent.parent, # defensive
    _MODULE_DIR,               # running from _data/ as root
]


# Mandatory acknowledgement labels — bilingual.
# The English label is shown below the German label in the UI.
ACKNOWLEDGEMENT_LABELS_DE: list[str] = [
    "Ich habe verstanden, dass dieses System KEIN Medizinprodukt "
    "(MDR 2017/745) und NICHT klinisch validiert ist.",
    "Ich habe verstanden, dass die Ausgaben KEINE Diagnose und "
    "KEINE Therapieempfehlung darstellen.",
    "Ich habe verstanden, dass die ärztliche bzw. "
    "psychotherapeutische Verantwortung bei qualifizierten "
    "Fachpersonen verbleibt.",
    "Ich nutze diese Software auf EIGENES RISIKO "
    "(Haftung beschränkt auf Vorsatz und grobe Fahrlässigkeit, "
    "§ 521 BGB).",
]

ACKNOWLEDGEMENT_LABELS_EN: list[str] = [
    "I understand that this system is NOT a medical device "
    "(MDR 2017/745) and NOT clinically validated.",
    "I understand that the outputs are NOT a diagnosis and "
    "NOT a therapy recommendation.",
    "I understand that clinical / psychotherapeutic responsibility "
    "remains with qualified professionals.",
    "I use this software AT MY OWN RISK "
    "(liability limited to intent and gross negligence, § 521 BGB).",
]


# Minimal fallback disclaimer if NOTICE file cannot be located.
_FALLBACK_DISCLAIMER_TEXT = (
    "Multiaxial Diagnostic Expert System — NOTICE (fallback)\n"
    "\n"
    "This software is NOT a medical device within the meaning of the "
    "EU MDR 2017/745. It is not clinically validated, not certified, "
    "and not approved by BfArM or any Notified Body.\n"
    "Outputs are structured coding proposals and pattern-based "
    "notifications, not clinical diagnoses or therapy recommendations.\n"
    "Clinical responsibility remains with qualified professionals.\n"
    "Use at your own risk. Liability limited to intent and gross "
    "negligence (§ 521 BGB).\n"
    "\n"
    "Diese Software ist KEIN Medizinprodukt im Sinne der EU-MDR "
    "2017/745. Keine klinische Validierung, keine Zertifizierung, "
    "keine Prüfung durch BfArM oder eine Benannte Stelle.\n"
    "Ausgaben sind strukturierte Kodierungsvorschläge und musterbasierte "
    "Hinweise, keine klinischen Diagnosen oder Therapieempfehlungen.\n"
    "Klinische Verantwortung verbleibt bei qualifizierten Fachpersonen.\n"
    "Nutzung auf eigenes Risiko. Haftung auf Vorsatz und grobe "
    "Fahrlässigkeit beschränkt (§ 521 BGB).\n"
)


def _find_notice_path() -> Optional[Path]:
    """Locate the NOTICE file in the repo root."""
    for candidate in _REPO_ROOT_CANDIDATES:
        notice = candidate / "NOTICE"
        if notice.is_file():
            return notice
    return None


def load_disclaimer_text() -> str:
    """Return the NOTICE text, or a static fallback."""
    path = _find_notice_path()
    if path is not None:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            pass
    return _FALLBACK_DISCLAIMER_TEXT


def compute_disclaimer_hash(text: Optional[str] = None) -> str:
    """SHA-256 (hex) of the disclaimer text."""
    if text is None:
        text = load_disclaimer_text()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def user_config_dir(app_name: str = "multiaxial-diagnostic") -> Path:
    """Return a per-user config directory suitable for a marker file.

    Uses ``%APPDATA%`` on Windows and ``~/.config`` elsewhere.
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )
    path = Path(base) / app_name
    return path


def marker_path(app_name: str = "multiaxial-diagnostic") -> Path:
    return user_config_dir(app_name) / ACK_MARKER_FILENAME


def load_marker(path: Optional[Path] = None) -> Optional[dict]:
    """Return the acknowledgement marker dict, or ``None``."""
    if path is None:
        path = marker_path()
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def is_accepted(
    current_hash: Optional[str] = None,
    path: Optional[Path] = None,
) -> bool:
    """Return ``True`` if a valid acknowledgement exists for the current text."""
    if current_hash is None:
        current_hash = compute_disclaimer_hash()
    marker = load_marker(path)
    if not marker:
        return False
    if marker.get("disclaimer_version") != DISCLAIMER_VERSION:
        return False
    if marker.get("disclaimer_hash") != current_hash:
        return False
    if not marker.get("accepted_at"):
        return False
    return True


def record_acceptance(
    *,
    text: Optional[str] = None,
    acknowledged_labels: Optional[list[str]] = None,
    path: Optional[Path] = None,
    timestamp: Optional[str] = None,
) -> dict:
    """Persist the acknowledgement and return the marker dict."""
    if text is None:
        text = load_disclaimer_text()
    disclaimer_hash = compute_disclaimer_hash(text)
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if path is None:
        path = marker_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    marker = {
        "event": "first_start_acknowledgement",
        "disclaimer_version": DISCLAIMER_VERSION,
        "disclaimer_hash": disclaimer_hash,
        "accepted_at": timestamp,
        "acknowledged_labels": acknowledged_labels
            or list(ACKNOWLEDGEMENT_LABELS_DE),
    }
    path.write_text(
        json.dumps(marker, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return marker


__all__ = [
    "ACKNOWLEDGEMENT_LABELS_DE",
    "ACKNOWLEDGEMENT_LABELS_EN",
    "ACK_MARKER_FILENAME",
    "DISCLAIMER_VERSION",
    "compute_disclaimer_hash",
    "is_accepted",
    "load_disclaimer_text",
    "load_marker",
    "marker_path",
    "record_acceptance",
    "user_config_dir",
]
