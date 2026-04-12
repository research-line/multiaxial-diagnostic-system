"""Streamlit integration for the first-start acknowledgement.

Renders a full-screen blocking disclaimer gate. While the user has not
accepted the current disclaimer text, no other part of the application
is rendered.

Usage in ``multiaxial_diagnostic_system.py``::

    from disclaimer_streamlit import require_disclaimer_acceptance
    require_disclaimer_acceptance()   # blocks until accepted

Place this call immediately after ``st.set_page_config(...)`` and
**before** any other UI is rendered.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from disclaimer_core import (
    ACKNOWLEDGEMENT_LABELS_DE,
    ACKNOWLEDGEMENT_LABELS_EN,
    compute_disclaimer_hash,
    is_accepted,
    load_disclaimer_text,
    record_acceptance,
)


_SESSION_KEY = "disclaimer_accepted"


def _render_gate(lang: str) -> None:
    """Render the full-screen blocking disclaimer gate."""
    labels = (
        ACKNOWLEDGEMENT_LABELS_DE if lang == "de" else ACKNOWLEDGEMENT_LABELS_EN
    )

    st.title(
        "Rechtlicher Hinweis / Legal Notice"
        if lang == "de"
        else "Legal Notice / Rechtlicher Hinweis"
    )
    st.warning(
        "Dieses System ist **kein Medizinprodukt** und dient ausschließlich "
        "Forschungs-, Lehr- und Softwareentwicklungszwecken. Bitte "
        "bestätigen Sie die vier Punkte unten, um fortzufahren."
        if lang == "de"
        else
        "This system is **not a medical device**. It is intended for "
        "research, teaching, and software engineering purposes only. "
        "Please acknowledge the four items below to continue."
    )

    with st.expander(
        "Vollständigen Haftungstext anzeigen / Show full legal text",
        expanded=False,
    ):
        st.text(load_disclaimer_text())

    st.markdown("---")
    st.subheader(
        "Pflicht-Bestätigungen" if lang == "de" else "Mandatory acknowledgements"
    )

    checks = []
    for idx, label in enumerate(labels):
        checks.append(
            st.checkbox(label, key=f"_disclaimer_cb_{idx}", value=False)
        )

    all_checked = all(checks)
    st.markdown("---")

    col_cancel, col_accept = st.columns([1, 1])
    with col_cancel:
        if st.button(
            "Ablehnen / Decline",
            key="_disclaimer_decline",
            use_container_width=True,
        ):
            st.error(
                "Ohne Bestätigung kann die Software nicht genutzt werden. "
                "Bitte schließen Sie den Browser-Tab."
                if lang == "de"
                else
                "Without acknowledgement the software cannot be used. "
                "Please close the browser tab."
            )
            st.stop()

    with col_accept:
        if st.button(
            "Bestätigen und fortfahren / Acknowledge and continue",
            key="_disclaimer_accept",
            disabled=not all_checked,
            type="primary",
            use_container_width=True,
        ):
            record_acceptance(
                text=load_disclaimer_text(),
                acknowledged_labels=labels,
            )
            st.session_state[_SESSION_KEY] = True
            st.rerun()


def require_disclaimer_acceptance(lang: Optional[str] = None) -> None:
    """Block further UI rendering until the disclaimer is accepted.

    Args:
        lang: Optional language code ("de" or "en"). If not given the
            session-state language is used (falls back to "de").
    """
    if st.session_state.get(_SESSION_KEY):
        return

    current_hash = compute_disclaimer_hash()
    if is_accepted(current_hash=current_hash):
        st.session_state[_SESSION_KEY] = True
        return

    if lang is None:
        lang = st.session_state.get("lang", "de")
    _render_gate(lang)
    # If the gate was rendered we must not let the caller continue.
    st.stop()


__all__ = ["require_disclaimer_acceptance"]
