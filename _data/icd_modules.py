"""External classification-catalogue bindings (ICD-10, ICD-10-CM, ICD-11).

Design rationale
----------------
The system does NOT maintain its own copy of the ICD catalogues. Re-typing a
classification into the repository would create a second, silently diverging
source of truth -- the classic failure mode of clinical coding tools. Instead
this module *binds* established external catalogue modules behind one uniform
interface, and reports honestly what is and is not available at runtime.

Providers
---------
ICD-10 (WHO 2019)   `simple_icd_10`      offline, public domain (CC0)
ICD-10-CM (US)      `simple_icd_10_cm`   offline, MIT wrapper over public-domain CDC/NCHS data
ICD-11 (WHO)        `simple_icd_11`      ONLINE ONLY -- requires WHO ICD-API OAuth2 credentials

Two properties are deliberate:

1. **Graceful degradation.** A missing package or missing WHO credentials never
   raises at import time. The provider simply reports `available() == False`
   with a human-readable reason, and callers fall back to the bundled seed
   catalogue in `diagnostic_codes.db`.

2. **Provenance is explicit.** Every provider states its source, licence,
   whether it works offline, and which release it serves. A coding proposal
   whose origin cannot be named is not a usable coding proposal.

WHO ICD-11 credentials
----------------------
Register (free) at https://icd.who.int/icdapi and export:

    WHO_ICD_CLIENT_ID=...
    WHO_ICD_CLIENT_SECRET=...

Without them the ICD-11 provider stays unavailable by design. The bundled
psychiatric seed catalogue remains the fallback so the application keeps
working offline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    "Provenance",
    "CatalogEntry",
    "CatalogProvider",
    "ICD10Provider",
    "ICD10CMProvider",
    "ICD11Provider",
    "get_provider",
    "available_providers",
    "provider_report",
]


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Provenance:
    """Where a code came from. Never fabricate this."""

    system: str          # "icd10" | "icd10cm" | "icd11"
    source: str          # human-readable origin
    licence: str
    offline: bool
    module: str          # the external package actually bound
    release: str = "unknown"
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "system": self.system,
            "source": self.source,
            "licence": self.licence,
            "offline": self.offline,
            "module": self.module,
            "release": self.release,
            "note": self.note,
        }


@dataclass(frozen=True)
class CatalogEntry:
    code: str
    title: str
    system: str
    provenance: Provenance
    parent: Optional[str] = None
    children: tuple = field(default_factory=tuple)

    def label(self) -> str:
        return f"{self.code} - {self.title}"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class CatalogProvider:
    """Uniform interface over an external classification module."""

    system = "abstract"

    def __init__(self) -> None:
        self._unavailable_reason: str = "not initialised"

    # -- capability -------------------------------------------------------
    def available(self) -> bool:
        raise NotImplementedError

    def unavailable_reason(self) -> str:
        return self._unavailable_reason

    def provenance(self) -> Optional[Provenance]:
        raise NotImplementedError

    # -- lookup -----------------------------------------------------------
    def is_valid(self, code: str) -> bool:
        raise NotImplementedError

    def describe(self, code: str) -> Optional[CatalogEntry]:
        raise NotImplementedError

    def search(self, term: str, limit: int = 50) -> list:
        """Substring search over titles. Returns a list of CatalogEntry."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# ICD-10 (WHO 2019) -- offline
# ---------------------------------------------------------------------------


class ICD10Provider(CatalogProvider):
    system = "icd10"

    def __init__(self) -> None:
        super().__init__()
        self._mod = None
        try:
            import simple_icd_10 as mod  # type: ignore
            self._mod = mod
        except ImportError as exc:
            self._unavailable_reason = f"package 'simple-icd-10' not installed ({exc})"

    def available(self) -> bool:
        return self._mod is not None

    def provenance(self) -> Optional[Provenance]:
        if not self.available():
            return None
        return Provenance(
            system="icd10",
            source="WHO ICD-10, 2019 release",
            licence="Public domain (CC0) data via the simple-icd-10 package",
            offline=True,
            module="simple-icd-10",
            release="ICD-10 (WHO) 2019",
        )

    def is_valid(self, code: str) -> bool:
        if not self.available():
            return False
        try:
            return bool(self._mod.is_valid_item(code))
        except Exception:
            return False

    def describe(self, code: str) -> Optional[CatalogEntry]:
        if not self.is_valid(code):
            return None
        try:
            title = self._mod.get_description(code)
            parent = self._mod.get_parent(code) or None
            children = tuple(self._mod.get_children(code) or ())
        except Exception:
            return None
        return CatalogEntry(
            code=code,
            title=title,
            system=self.system,
            provenance=self.provenance(),
            parent=parent,
            children=children,
        )

    def search(self, term: str, limit: int = 50) -> list:
        if not self.available() or not term:
            return []
        needle = term.strip().lower()
        hits: list = []
        try:
            codes = self._mod.get_all_codes(with_dots=True)
        except Exception:
            return []
        for code in codes:
            try:
                title = self._mod.get_description(code)
            except Exception:
                continue
            if needle in title.lower() or needle in code.lower():
                entry = CatalogEntry(
                    code=code,
                    title=title,
                    system=self.system,
                    provenance=self.provenance(),
                )
                hits.append(entry)
                if len(hits) >= limit:
                    break
        return hits


# ---------------------------------------------------------------------------
# ICD-10-CM (US clinical modification) -- offline
# ---------------------------------------------------------------------------


class ICD10CMProvider(CatalogProvider):
    system = "icd10cm"

    def __init__(self) -> None:
        super().__init__()
        self._mod = None
        try:
            import simple_icd_10_cm as mod  # type: ignore
            self._mod = mod
        except ImportError as exc:
            self._unavailable_reason = f"package 'simple-icd-10-cm' not installed ({exc})"

    def available(self) -> bool:
        return self._mod is not None

    def provenance(self) -> Optional[Provenance]:
        if not self.available():
            return None
        return Provenance(
            system="icd10cm",
            source="ICD-10-CM (CDC/NCHS, US clinical modification)",
            licence="Public-domain US federal data; MIT-licensed Python wrapper",
            offline=True,
            module="simple-icd-10-cm",
            release=self._release(),
            note=(
                "The packaged release lags the current CDC/NCHS fiscal-year release. "
                "For billing-relevant coding, verify against the current official release."
            ),
        )

    def _release(self) -> str:
        try:
            import importlib.metadata as md
            return f"simple-icd-10-cm {md.version('simple-icd-10-cm')}"
        except Exception:
            return "unknown"

    def is_valid(self, code: str) -> bool:
        if not self.available():
            return False
        try:
            return bool(self._mod.is_valid_item(code))
        except Exception:
            return False

    def describe(self, code: str) -> Optional[CatalogEntry]:
        if not self.is_valid(code):
            return None
        try:
            title = self._mod.get_description(code)
            parent = self._mod.get_parent(code) or None
            children = tuple(self._mod.get_children(code) or ())
        except Exception:
            return None
        return CatalogEntry(
            code=code,
            title=title,
            system=self.system,
            provenance=self.provenance(),
            parent=parent,
            children=children,
        )

    def search(self, term: str, limit: int = 50) -> list:
        if not self.available() or not term:
            return []
        needle = term.strip().lower()
        hits: list = []
        try:
            codes = self._mod.get_all_codes(with_dots=True)
        except Exception:
            return []
        for code in codes:
            try:
                title = self._mod.get_description(code)
            except Exception:
                continue
            if needle in title.lower() or needle in code.lower():
                hits.append(
                    CatalogEntry(
                        code=code,
                        title=title,
                        system=self.system,
                        provenance=self.provenance(),
                    )
                )
                if len(hits) >= limit:
                    break
        return hits


# ---------------------------------------------------------------------------
# ICD-11 (WHO) -- ONLINE, requires OAuth2 credentials
# ---------------------------------------------------------------------------


class ICD11Provider(CatalogProvider):
    """Binds the official WHO ICD-11 API via `simple_icd_11`.

    Unlike the ICD-10 providers this one cannot work offline: the WHO API is the
    authoritative source and requires OAuth2 client credentials. Without them the
    provider reports unavailable and callers fall back to the bundled seed
    catalogue -- it does NOT silently invent codes.
    """

    system = "icd11"

    ENV_ID = "WHO_ICD_CLIENT_ID"
    ENV_SECRET = "WHO_ICD_CLIENT_SECRET"

    def __init__(self, language: str = "en", release: Optional[str] = None) -> None:
        super().__init__()
        self._explorer = None
        self._language = language
        self._release = release

        try:
            import simple_icd_11 as mod  # type: ignore
        except ImportError as exc:
            self._unavailable_reason = f"package 'simple-icd-11' not installed ({exc})"
            return

        client_id = os.environ.get(self.ENV_ID, "").strip()
        client_secret = os.environ.get(self.ENV_SECRET, "").strip()
        if not client_id or not client_secret:
            self._unavailable_reason = (
                f"WHO ICD-API credentials missing: set {self.ENV_ID} and {self.ENV_SECRET}. "
                "Register free at https://icd.who.int/icdapi. "
                "Falling back to the bundled psychiatric seed catalogue."
            )
            return

        try:
            self._explorer = mod.ICDExplorer(
                language=language,
                clientId=client_id,
                clientSecret=client_secret,
                release=release,
            )
        except Exception as exc:  # network down, bad credentials, WHO outage
            self._explorer = None
            self._unavailable_reason = f"WHO ICD-API handshake failed: {exc}"

    def available(self) -> bool:
        return self._explorer is not None

    def provenance(self) -> Optional[Provenance]:
        if not self.available():
            return None
        try:
            release = self._explorer.getRelease()
        except Exception:
            release = self._release or "unknown"
        return Provenance(
            system="icd11",
            source="WHO ICD-11 API (icd.who.int/icdapi), authoritative live source",
            licence="CC BY-ND 3.0 IGO (WHO)",
            offline=False,
            module="simple-icd-11",
            release=str(release),
            note="Live API. Requires OAuth2 credentials and network access.",
        )

    def is_valid(self, code: str) -> bool:
        if not self.available():
            return False
        try:
            return bool(self._explorer.isValidCode(code))
        except Exception:
            return False

    def describe(self, code: str) -> Optional[CatalogEntry]:
        if not self.available():
            return None
        try:
            entity = self._explorer.getEntityFromCode(code)
        except Exception:
            return None
        if entity is None:
            return None
        try:
            title = entity.getTitle()
        except Exception:
            return None
        parent = None
        children: tuple = ()
        try:
            parents = entity.getParent() or []
            if parents:
                parent = getattr(parents[0], "getCode", lambda: None)()
        except Exception:
            pass
        try:
            kids = entity.getChild() or []
            children = tuple(
                c for c in (getattr(k, "getCode", lambda: None)() for k in kids) if c
            )
        except Exception:
            pass
        return CatalogEntry(
            code=code,
            title=title,
            system=self.system,
            provenance=self.provenance(),
            parent=parent,
            children=children,
        )

    def search(self, term: str, limit: int = 50) -> list:
        """The WHO API exposes lookup by code/id, not a free-text index here.

        Returning an empty list is the honest answer: we do not fake a search
        over a live catalogue we cannot enumerate. Callers should use the
        bundled seed catalogue for browsing and this provider for verification.
        """
        return []


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


_REGISTRY = {
    "icd10": ICD10Provider,
    "icd10cm": ICD10CMProvider,
    "icd11": ICD11Provider,
}

_CACHE: dict = {}


def get_provider(system: str, **kwargs):
    """Return a (cached) provider. Never raises for a missing dependency."""
    key = system.lower()
    if key not in _REGISTRY:
        raise KeyError(f"unknown classification system: {system!r}")
    cache_key = (key, tuple(sorted(kwargs.items())))
    if cache_key not in _CACHE:
        _CACHE[cache_key] = _REGISTRY[key](**kwargs)
    return _CACHE[cache_key]


def available_providers() -> list:
    """Systems whose external module is bound and usable right now."""
    return [name for name in _REGISTRY if get_provider(name).available()]


def provider_report() -> list:
    """Capability report -- what is bound, what is not, and why.

    Rendered in the UI so the clinician always knows which catalogue actually
    answered, rather than trusting an unlabelled code.
    """
    report = []
    for name in _REGISTRY:
        p = get_provider(name)
        prov = p.provenance()
        report.append(
            {
                "system": name,
                "available": p.available(),
                "reason": "" if p.available() else p.unavailable_reason(),
                "provenance": prov.as_dict() if prov else None,
            }
        )
    return report


if __name__ == "__main__":  # pragma: no cover - manual smoke check
    import json

    print(json.dumps(provider_report(), indent=2, ensure_ascii=False))
