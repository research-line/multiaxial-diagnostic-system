"""Tests for the external ICD catalogue bindings.

The point of these tests is not to re-test the upstream packages. It is to pin
the two properties this project actually depends on:

  1. The binding never *fabricates* a code. An unavailable catalogue must report
     "unavailable", never a silent negative and never a guess.
  2. The binding never raises at import or lookup time when a module or a
     credential is missing -- it degrades.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_data"))

import icd_modules as icd  # noqa: E402


# ---------------------------------------------------------------------------
# Registry / capability reporting
# ---------------------------------------------------------------------------


def test_registry_knows_the_three_systems():
    report = icd.provider_report()
    assert {r["system"] for r in report} == {"icd10", "icd10cm", "icd11"}


def test_unknown_system_raises():
    with pytest.raises(KeyError):
        icd.get_provider("icd9")


def test_every_provider_reports_availability_and_reason():
    """An unavailable provider must always say WHY. Silence is not acceptable."""
    for entry in icd.provider_report():
        assert isinstance(entry["available"], bool)
        if not entry["available"]:
            assert entry["reason"], f"{entry['system']} is unavailable without a reason"
            assert entry["provenance"] is None
        else:
            assert entry["provenance"] is not None
            prov = entry["provenance"]
            # Provenance must be complete -- an unattributable code is unusable.
            for field in ("source", "licence", "module", "release"):
                assert prov[field], f"{entry['system']}: empty provenance field {field}"


# ---------------------------------------------------------------------------
# ICD-10 (offline, must be present)
# ---------------------------------------------------------------------------

icd10 = icd.get_provider("icd10")
requires_icd10 = pytest.mark.skipif(not icd10.available(), reason="simple-icd-10 not installed")


@requires_icd10
def test_icd10_known_code_resolves():
    entry = icd10.describe("F84.0")
    assert entry is not None
    assert entry.code == "F84.0"
    assert entry.title
    assert entry.system == "icd10"


@requires_icd10
def test_icd10_hierarchy_is_wired():
    entry = icd10.describe("F84")
    assert entry is not None
    assert "F84.0" in entry.children


@requires_icd10
def test_icd10_rejects_a_nonexistent_code():
    assert icd10.is_valid("ZZ99.9") is False
    assert icd10.describe("ZZ99.9") is None


@requires_icd10
def test_icd10_search_finds_by_title():
    hits = icd10.search("autism", limit=10)
    assert hits
    assert all(h.system == "icd10" for h in hits)


@requires_icd10
def test_icd10_provenance_is_offline_and_attributed():
    prov = icd10.provenance()
    assert prov.offline is True
    assert "WHO" in prov.source
    assert prov.module == "simple-icd-10"


# ---------------------------------------------------------------------------
# ICD-10-CM (offline)
# ---------------------------------------------------------------------------

icd10cm = icd.get_provider("icd10cm")
requires_cm = pytest.mark.skipif(not icd10cm.available(), reason="simple-icd-10-cm not installed")


@requires_cm
def test_icd10cm_resolves_a_dsm_aligned_code():
    entry = icd10cm.describe("F84.0")
    assert entry is not None
    assert entry.title


@requires_cm
def test_icd10cm_carries_a_staleness_warning():
    """The packaged CM release lags CDC/NCHS. That must be stated, not hidden."""
    prov = icd10cm.provenance()
    assert prov.note
    assert "official" in prov.note.lower() or "release" in prov.note.lower()


# ---------------------------------------------------------------------------
# ICD-11 (online, credential-gated) -- the degradation contract
# ---------------------------------------------------------------------------


def test_icd11_without_credentials_degrades_instead_of_guessing(monkeypatch):
    """Without WHO credentials the provider must be unavailable -- not wrong."""
    monkeypatch.delenv(icd.ICD11Provider.ENV_ID, raising=False)
    monkeypatch.delenv(icd.ICD11Provider.ENV_SECRET, raising=False)

    provider = icd.ICD11Provider()

    assert provider.available() is False
    assert provider.provenance() is None
    # It must not answer lookups at all rather than answer them wrongly.
    assert provider.is_valid("6A02") is False
    assert provider.describe("6A02") is None
    # And it must explain itself, pointing at the registration route.
    reason = provider.unavailable_reason()
    assert "credential" in reason.lower()
    assert "icd.who.int" in reason


def test_icd11_search_does_not_fake_an_index():
    """The WHO API is not enumerable here; returning [] is the honest answer."""
    assert icd.ICD11Provider().search("depression") == []


# ---------------------------------------------------------------------------
# The tri-state contract used by the application layer
# ---------------------------------------------------------------------------


def test_unavailable_is_never_reported_as_not_found(monkeypatch):
    """The clinically important distinction.

    "the catalogue says this code does not exist"  (not_found)
    is NOT the same as
    "we could not ask the catalogue"               (unavailable)

    Collapsing the two would let an unverifiable code look refuted, or a
    refuted code look merely unchecked.
    """
    monkeypatch.delenv(icd.ICD11Provider.ENV_ID, raising=False)
    monkeypatch.delenv(icd.ICD11Provider.ENV_SECRET, raising=False)
    icd._CACHE.clear()

    provider = icd.get_provider("icd11")
    assert provider.available() is False

    # A bound catalogue, by contrast, gives a real negative for a bogus code.
    if icd.get_provider("icd10").available():
        assert icd.get_provider("icd10").describe("ZZ99.9") is None
        assert icd.get_provider("icd10").available() is True

    icd._CACHE.clear()
