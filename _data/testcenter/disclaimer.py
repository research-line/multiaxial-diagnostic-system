"""First-start acknowledgement for the Flask Testcenter.

Provides a ``/disclaimer`` route and a ``before_request`` hook that
redirects users there until the four mandatory acknowledgements have
been given.

Accepted state is stored in two places:

1. **Flask session cookie** (``disclaimer_accepted``) — primary gate,
   per-browser.
2. **Server-side marker file** (``disclaimer_core.marker_path``) —
   secondary record for the administrator who first runs the app.

Design rationale: the Testcenter is used by clinicians (admin) and
by clients (patients) filling out tests via shared tokens. Clients
only need a lightweight per-session acknowledgement; the persistent
marker primarily serves the clinician.
"""
from __future__ import annotations

import sys
from pathlib import Path

from flask import (Blueprint, current_app, redirect, render_template_string,
                   request, session, url_for)

# Import the framework-agnostic core. The core lives in _data/.
_THIS_DIR = Path(__file__).resolve().parent
_DATA_DIR = _THIS_DIR.parent
if str(_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(_DATA_DIR))

from disclaimer_core import (  # noqa: E402
    ACKNOWLEDGEMENT_LABELS_DE,
    ACKNOWLEDGEMENT_LABELS_EN,
    compute_disclaimer_hash,
    is_accepted as file_marker_accepted,
    load_disclaimer_text,
    record_acceptance,
)

_SESSION_KEY = "disclaimer_accepted"
_SESSION_HASH_KEY = "disclaimer_hash"

disclaimer_bp = Blueprint("disclaimer", __name__)


# Paths that never require acknowledgement (the disclaimer itself,
# static assets, and client-facing read-only endpoints).
_EXEMPT_PREFIXES = (
    "/disclaimer",
    "/static/",
    # client-facing (anonymous) endpoints — clients acknowledge via
    # a lightweight per-session cookie on their first POST/GET
)


_TEMPLATE = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Rechtlicher Hinweis — Multiaxial Diagnostic Testcenter</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;
     max-width:820px;margin:2em auto;padding:1.5em;color:#222;}
h1{color:#8b0000;}
.box{background:#fdf6e3;border-left:5px solid #b58900;
     padding:1em 1.2em;border-radius:4px;margin:1em 0;}
pre{background:#f6f6f6;padding:1em;border-radius:4px;
    white-space:pre-wrap;font-size:0.85em;max-height:260px;
    overflow-y:auto;}
label{display:block;margin:0.6em 0;cursor:pointer;
      padding:0.4em;border-radius:3px;}
label:hover{background:#f0f0f0;}
.buttons{display:flex;gap:1em;margin-top:1.5em;}
button{padding:0.7em 1.4em;font-size:1em;border:none;
       border-radius:4px;cursor:pointer;}
button.accept{background:#268bd2;color:white;}
button.accept:disabled{background:#ccc;cursor:not-allowed;}
button.reject{background:#eee;color:#333;}
.lang{font-size:0.85em;color:#666;margin-left:0.4em;}
</style>
</head>
<body>
<h1>Rechtlicher Hinweis / Legal Notice</h1>
<div class="box">
<strong>Kein Medizinprodukt / Not a medical device.</strong><br>
Diese Software dient ausschließlich Forschungs-, Lehr- und
Softwareentwicklungszwecken. Bitte bestätigen Sie alle vier Punkte
unten, um das Testcenter zu nutzen.
<br><br>
This software is intended for research, teaching, and software
engineering purposes only. Please acknowledge all four items below
to use the Testcenter.
</div>

<details>
<summary>Vollständigen Haftungstext anzeigen / Show full legal text</summary>
<pre>{{ notice_text }}</pre>
</details>

<form method="POST" action="{{ url_for('disclaimer.disclaimer_view') }}">
<input type="hidden" name="next" value="{{ next_url }}">
<h2>Pflicht-Bestätigungen / Mandatory acknowledgements</h2>
{% for idx in range(labels_de|length) %}
<label>
  <input type="checkbox" name="ack_{{ idx }}" value="1" required>
  {{ labels_de[idx] }}<br>
  <span class="lang">{{ labels_en[idx] }}</span>
</label>
{% endfor %}

<div class="buttons">
  <button type="submit" class="accept">
    Bestätigen und fortfahren / Acknowledge and continue
  </button>
  <a href="about:blank" class="reject"
     style="text-decoration:none;padding:0.7em 1.4em;
            background:#eee;color:#333;border-radius:4px;">
    Ablehnen / Decline
  </a>
</div>
</form>

<p style="font-size:0.8em;color:#666;margin-top:2em;">
Version: {{ disclaimer_hash[:12] }} — bei Änderungen des
Haftungstextes ist eine erneute Bestätigung erforderlich.<br>
Liability limited to intent and gross negligence (§ 521 BGB).
</p>
</body>
</html>
"""


def _safe_next(default: str = "/") -> str:
    candidate = request.values.get("next") or request.path
    if not candidate or not candidate.startswith("/"):
        return default
    if candidate.startswith("//"):
        return default
    return candidate


@disclaimer_bp.route("/disclaimer", methods=["GET", "POST"])
def disclaimer_view():
    current_hash = compute_disclaimer_hash()

    if request.method == "POST":
        all_checked = all(
            request.form.get(f"ack_{i}") == "1"
            for i in range(len(ACKNOWLEDGEMENT_LABELS_DE))
        )
        if all_checked:
            session[_SESSION_KEY] = True
            session[_SESSION_HASH_KEY] = current_hash
            # Persist server-side marker too (harmless if already present)
            try:
                record_acceptance(
                    text=load_disclaimer_text(),
                    acknowledged_labels=list(ACKNOWLEDGEMENT_LABELS_DE),
                )
            except OSError:
                # Marker persistence is best-effort; session state is
                # authoritative for the gate.
                pass
            return redirect(_safe_next("/"))
        # fall through to re-render

    return render_template_string(
        _TEMPLATE,
        notice_text=load_disclaimer_text(),
        labels_de=ACKNOWLEDGEMENT_LABELS_DE,
        labels_en=ACKNOWLEDGEMENT_LABELS_EN,
        next_url=_safe_next("/"),
        disclaimer_hash=current_hash,
    )


def _gate_before_request():
    """Redirect unauthenticated users to the disclaimer page."""
    path = request.path or "/"
    for prefix in _EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return None

    current_hash = compute_disclaimer_hash()
    if session.get(_SESSION_KEY) and session.get(_SESSION_HASH_KEY) == current_hash:
        return None

    # Allow clinician to inherit the server-side acceptance on first visit.
    if file_marker_accepted(current_hash=current_hash):
        session[_SESSION_KEY] = True
        session[_SESSION_HASH_KEY] = current_hash
        return None

    return redirect(
        url_for("disclaimer.disclaimer_view", next=path)
    )


def register_disclaimer(app) -> None:
    """Register the blueprint and the before_request gate on *app*."""
    app.register_blueprint(disclaimer_bp)
    app.before_request(_gate_before_request)


__all__ = ["disclaimer_bp", "register_disclaimer"]
