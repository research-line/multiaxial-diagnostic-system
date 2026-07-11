"""End-to-end checks of the running Streamlit app.

Two things are pinned here that unit tests cannot see:

1. **The legal gate actually gates.** The disclaimer used to be skipped silently
   whenever `disclaimer_core` failed to import -- which happened whenever the app
   was launched from a working directory other than `_data/`. A medical-adjacent
   tool must never render its clinical surface without the acknowledgement.

2. **The catalogue bindings are real.** The ICD-10 answer must come from the
   external module, a bogus code must be a real negative, and ICD-11 must degrade
   honestly when WHO credentials are absent -- never silently "verify" nothing.
"""

import os
import sys
import tempfile

import pytest

pytest.importorskip("streamlit", reason="streamlit not installed")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "_data", "multiaxial_diagnostic_system.py")
sys.path.insert(0, os.path.join(ROOT, "_data"))


@pytest.fixture()
def clean_profile(monkeypatch):
    """Isolate the acknowledgement marker so the gate starts closed."""
    tmp = tempfile.mkdtemp(prefix="diag_test_")
    monkeypatch.setenv("APPDATA", tmp)
    monkeypatch.setenv("XDG_CONFIG_HOME", tmp)
    monkeypatch.delenv("WHO_ICD_CLIENT_ID", raising=False)
    monkeypatch.delenv("WHO_ICD_CLIENT_SECRET", raising=False)
    return tmp


def _run(timeout=120):
    at = AppTest.from_file(APP, default_timeout=timeout)
    at.run()
    assert not at.exception, f"app raised: {at.exception}"
    return at


def test_disclaimer_gate_blocks_the_app_on_a_clean_profile(clean_profile):
    at = _run()
    assert len(at.checkbox) == 4, "the four acknowledgements must be required"
    assert any(b.key == "_disclaimer_accept" for b in at.button)
    assert not at.sidebar.radio, "navigation must not be reachable before acknowledgement"


def test_app_renders_after_acknowledgement(clean_profile):
    import disclaimer_core as dc

    dc.record_acceptance()
    at = _run()
    assert at.sidebar.radio, "navigation should be reachable after acknowledgement"


def _catalog_page(clean_profile):
    import disclaimer_core as dc

    dc.record_acceptance()
    at = _run()
    radio = at.sidebar.radio[0]
    target = [o for o in radio.options if "Katalog" in o or "Catalogue" in o]
    assert target, f"catalogue page missing: {list(radio.options)}"
    radio.set_value(target[0]).run()
    assert not at.exception, f"catalogue page raised: {at.exception}"
    return at


def test_catalogue_page_reports_bindings_truthfully(clean_profile):
    at = _catalog_page(clean_profile)
    labels = [e.label for e in at.expander]

    # Offline modules must be bound...
    assert any(l.upper().startswith("✅ ICD10 ") for l in labels), labels
    assert any("ICD10CM" in l.upper() and "✅" in l for l in labels), labels
    # ...and the credential-gated one must say so instead of pretending.
    assert any("ICD11" in l.upper() and "⚠️" in l for l in labels), labels


def test_real_code_is_verified_against_the_external_catalogue(clean_profile):
    at = _catalog_page(clean_profile)
    field = [x for x in at.text_input if x.key == "cat_verify_code"][0]
    field.set_value("F84.0").run()
    assert not at.exception
    assert any("F84.0" in s.value for s in at.success)


def test_bogus_code_is_a_real_negative_not_a_silent_pass(clean_profile):
    at = _catalog_page(clean_profile)
    field = [x for x in at.text_input if x.key == "cat_verify_code"][0]
    field.set_value("ZZ99.9").run()
    assert [e for e in at.error], "bogus code must be reported as not found"
    assert not [s for s in at.success if "ZZ99" in s.value], \
        "a bogus code must never be reported as verified"


def test_catalogue_search_returns_plausible_hits(clean_profile):
    at = _catalog_page(clean_profile)
    field = [x for x in at.text_input if x.key == "cat_search_term"]
    if not field:
        pytest.skip("no searchable catalogue bound")
    field[0].set_value("autism").run()
    assert not at.exception
    body = " ".join(m.value for m in at.markdown)
    assert "F84" in body, "ICD-10 search should surface the F84 block for 'autism'"
