"""
==========================================================================================
KLINISCHES MULTIAXIALES EXPERTENSYSTEM (DSM-5-TR / ICD-11 / MULTIAXIAL V10)
==========================================================================================

Computergestütztes 6-Achsen-Diagnostiksystem basierend auf:
- DSM-5-TR Cross-Cutting Symptom Measures (Level 1 & 2)
- Michael B. Firsts 6-Stufen-Gatekeeper-Logik
- ICD-11 / DSM-5-TR Dual-System-Architektur
- ICF / WHODAS 2.0 / GdB Funktionsbeurteilung
- PID-5-BF+M dimensionale Persönlichkeitsdiagnostik
- HiTOP-Spektren (Kotov et al., 2017) aus Cross-Cutting-Daten
- Hierarchische Zustandsmaschine (HSM) als Entscheidungsmotor

V9.1: Symmetrische Achse III (13 Subachsen), HiTOP-Integration, Ii/Ij-Swap
      Bilingual (Deutsch / English) via translations.json
      XSS-Schutz, formale Coverage Analysis, WHODAS-Persistenz, GAF-Deprecation
V10:  Sprint 2 - Strukturierte 3P/4P-Kodierung, Pathophysiologisches Kausalmodell,
      Therapieresistenz-Tracking, CGI-S/I Verlaufsparameter, Session Auto-Save

Technologie: transitions (HSM), Streamlit (UI), anytree (Visualisierung),
             Plotly (PID-5 + HiTOP Radar), Pydantic (Datenvalidierung)

Aufbauend auf V8 / Vorläuferscript icf11dsm5.py (V6 Expert System)
==========================================================================================
"""

import streamlit as st
import datetime
import html as html_mod
import json
import math
import os
from dataclasses import dataclass, field, asdict
from typing import Optional
try:
    from transitions.extensions import HierarchicalMachine
    HAS_TRANSITIONS = True
except ImportError:
    HAS_TRANSITIONS = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from anytree import Node, RenderTree
    HAS_ANYTREE = True
except ImportError:
    HAS_ANYTREE = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

import sqlite3

# ===================================================================
# DIAGNOSTIC CODE DATABASE
# ===================================================================

_CODE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostic_codes.db")
HAS_CODE_DB = os.path.exists(_CODE_DB_PATH)


_VALID_TITLE_COLS = {"title_de", "title_en"}


@st.cache_data(ttl=3600)
def _load_code_options(system: str, lang: str = "de") -> list:
    """Load all codes from a system as 'CODE - Title' strings for selectbox."""
    if not HAS_CODE_DB:
        return []
    title_col = "title_de" if lang == "de" else "title_en"
    if title_col not in _VALID_TITLE_COLS:
        return []
    conn = None
    try:
        conn = sqlite3.connect(_CODE_DB_PATH)
        if system == "icd11":
            rows = conn.execute(
                f"SELECT code, {title_col} FROM icd11 ORDER BY code"
            ).fetchall()
        elif system == "dsm5":
            rows = conn.execute(
                f"SELECT icd10cm_code, {title_col} FROM dsm5 ORDER BY icd10cm_code"
            ).fetchall()
        elif system == "icf":
            rows = conn.execute(
                f"SELECT code, {title_col} FROM icf ORDER BY code"
            ).fetchall()
        else:
            rows = []
    except Exception:
        rows = []
    finally:
        if conn:
            conn.close()
    return [f"{code} - {title}" for code, title in rows]


@st.cache_data(ttl=3600)
def _load_icd11_options_by_chapter(chapter: str, lang: str = "de") -> list:
    """Load ICD-11 codes filtered by chapter."""
    if not HAS_CODE_DB:
        return []
    title_col = "title_de" if lang == "de" else "title_en"
    if title_col not in _VALID_TITLE_COLS:
        return []
    conn = None
    try:
        conn = sqlite3.connect(_CODE_DB_PATH)
        rows = conn.execute(
            f"SELECT code, {title_col} FROM icd11 WHERE chapter = ? ORDER BY code",
            (chapter,)
        ).fetchall()
    except Exception:
        rows = []
    finally:
        if conn:
            conn.close()
    return [f"{code} - {title}" for code, title in rows]


def get_cross_mapped_code(from_system: str, from_code: str, to_system: str) -> str:
    """Look up cross-mapped code between systems.

    Tries forward lookup first (from_system -> to_system),
    then reverse lookup (maybe stored as to_system -> from_system in DB).
    """
    if not HAS_CODE_DB:
        return ""
    conn = None
    try:
        conn = sqlite3.connect(_CODE_DB_PATH)
        # Forward: from_system/from_code -> to_system
        row = conn.execute(
            "SELECT target_code FROM code_mapping "
            "WHERE source_system=? AND source_code=? AND target_system=? LIMIT 1",
            (from_system, from_code, to_system)
        ).fetchone()
        if not row:
            # Reverse: maybe stored as to_system -> from_system in DB
            # So from_system is the DB's target_system, from_code is the DB's target_code,
            # and to_system is the DB's source_system. We return the DB's source_code.
            row = conn.execute(
                "SELECT source_code FROM code_mapping "
                "WHERE target_system=? AND target_code=? AND source_system=? LIMIT 1",
                (from_system, from_code, to_system)
            ).fetchone()
        return row[0] if row else ""
    except Exception:
        return ""
    finally:
        if conn:
            conn.close()


def get_code_title(system: str, code: str, lang: str = "de") -> str:
    """Get the title for a specific code."""
    if not HAS_CODE_DB:
        return ""
    title_col = "title_de" if lang == "de" else "title_en"
    if title_col not in _VALID_TITLE_COLS:
        return ""
    conn = None
    try:
        conn = sqlite3.connect(_CODE_DB_PATH)
        if system == "icd11":
            row = conn.execute(f"SELECT {title_col} FROM icd11 WHERE code=?", (code,)).fetchone()
        elif system == "dsm5":
            row = conn.execute(f"SELECT {title_col} FROM dsm5 WHERE icd10cm_code=?", (code,)).fetchone()
        elif system == "icf":
            row = conn.execute(f"SELECT {title_col} FROM icf WHERE code=?", (code,)).fetchone()
        else:
            row = None
        return row[0] if row else ""
    except Exception:
        return ""
    finally:
        if conn:
            conn.close()


def _extract_code(option: str) -> str:
    """Extract code from 'CODE - Title' selectbox format."""
    if option and " - " in option:
        return option.split(" - ")[0].strip()
    return option.strip() if option else ""


def esc(text) -> str:
    """Escape user-supplied text for safe HTML embedding."""
    return html_mod.escape(str(text)) if text else ""


# ===================================================================
# TRANSLATION SYSTEM (i18n)
# ===================================================================

_TRANSLATIONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations.json")
with open(_TRANSLATIONS_PATH, "r", encoding="utf-8") as _f:
    TRANSLATIONS = json.load(_f)


def t(key: str) -> str:
    """Return translated string for current language."""
    lang = st.session_state.get("lang", "de")
    return TRANSLATIONS.get(lang, TRANSLATIONS["de"]).get(key, key)


# ===================================================================
# DATENMODELLE (Pydantic-artig mit dataclasses)
# ===================================================================

@dataclass
class Diagnosis:
    code_icd11: str = ""
    code_dsm5: str = ""
    name: str = ""
    status: str = "akut"
    evidence: str = ""
    date_onset: str = ""
    date_remission: str = ""
    remission_factors: list = field(default_factory=list)
    treatment_history: list = field(default_factory=list)
    # NEU: PRO/CONTRA-Evidenzbewertung & Konfidenz (aus FALLBEZOGENE_AUSWERTUNG)
    confidence_pct: int = 0
    severity: str = ""
    evidence_pro: str = ""
    evidence_contra: str = ""


@dataclass
class PID5Profile:
    negative_affectivity: float = 0.0
    detachment: float = 0.0
    antagonism: float = 0.0
    disinhibition: float = 0.0
    psychoticism: float = 0.0
    anankastia: float = 0.0  # ICD-11 Erweiterung (PID-5-BF+M)


@dataclass
class MedicalCondition:
    name: str = ""
    icd11_code: str = ""
    dsm5_code: str = ""
    causality: str = "beitragend"
    evidence: str = ""
    status: str = "aktiv"
    date_onset: str = ""
    date_remission: str = ""
    remission_factors: list = field(default_factory=list)


@dataclass
class MedicationEntry:
    name: str = ""
    dose: str = ""
    unit: str = ""
    purpose: str = ""
    since: str = ""
    effect: str = ""
    effect_rating: int = 5
    side_effects: str = ""
    interactions: str = ""
    schedule: str = ""


@dataclass
class CaveAlert:
    text: str = ""
    category: str = ""
    axis_ref: str = ""
    date_added: str = ""


@dataclass
class SymptomCoverage:
    symptom: str = ""
    explaining_diagnoses: str = ""
    coverage_pct: int = 0


@dataclass
class InvestigationPlan:
    investigation: str = ""
    fachgebiet: str = ""
    priority: str = ""
    reason: str = ""
    status: str = "offen"


@dataclass
class SymptomTimeline:
    symptom: str = ""
    onset: str = ""
    current_status: str = ""
    therapy_response: str = ""


@dataclass
class HiTOPProfile:
    internalizing: float = 0.0
    thought_disorder: float = 0.0
    disinhibited_externalizing: float = 0.0
    antagonistic_externalizing: float = 0.0
    detachment: float = 0.0
    somatoform: float = 0.0


@dataclass
class FunctioningAssessment:
    gaf_score: int = 0
    whodas_cognition: int = 0
    whodas_mobility: int = 0
    whodas_selfcare: int = 0
    whodas_getting_along: int = 0
    whodas_life_activities: int = 0
    whodas_participation: int = 0
    gdb_score: int = 0
    psychosocial_stressors: list = field(default_factory=list)


@dataclass
class EvidenceEntry:
    axis: str = ""
    document_type: str = ""
    description: str = ""
    assessment: str = ""
    date: str = ""
    source: str = ""


@dataclass
class ContactPerson:
    name: str = ""
    role: str = ""          # Elternteil, Partner, Hausarzt, Facharzt, Therapeut, etc.
    institution: str = ""
    phone: str = ""
    notes: str = ""


@dataclass
class FormativeExperience:
    description: str = ""
    age_period: str = ""
    impact: str = ""
    date_added: str = ""


@dataclass
class CoreConflict:
    conflict: str = ""
    description: str = ""
    date_added: str = ""


@dataclass
class ContactLog:
    date: str = ""
    contact_type: str = ""   # Telefonat, Gespräch, Beobachtung, Hausbesuch, Fremdanamnese
    contact_person: str = ""
    content: str = ""
    axis_ref: str = ""


@dataclass
class StructuredFactor:
    text: str = ""
    source_axis: str = ""
    evidence_level: str = ""


@dataclass
class PathophysiologicalModel:
    genetic_neurobiological: str = ""
    psychological_developmental: str = ""
    environmental_situational: str = ""


@dataclass
class TreatmentAttempt:
    treatment: str = ""
    treatment_type: str = ""
    start_date: str = ""
    end_date: str = ""
    response: str = ""
    reason_stopped: str = ""
    notes: str = ""


@dataclass
class CGIAssessment:
    date: str = ""
    cgi_s: int = 0
    cgi_i: int = 0
    therapeutic_effect: int = 0
    side_effects: int = 0
    notes: str = ""


@dataclass
class ConditionModel:
    predisposing: list = field(default_factory=list)
    precipitating: list = field(default_factory=list)
    perpetuating: list = field(default_factory=list)
    protective: list = field(default_factory=list)
    narrative: str = ""


@dataclass
class PatientData:
    # Intake-Daten (Gate 0)
    patient_name: str = ""
    patient_dob: str = ""
    presenting_complaint: str = ""

    # Achse I: Psychische Profile
    diagnoses_acute: list = field(default_factory=list)
    diagnoses_chronic: list = field(default_factory=list)
    diagnoses_remitted: list = field(default_factory=list)
    diagnoses_suspected: list = field(default_factory=list)
    diagnoses_excluded: list = field(default_factory=list)
    treatment_history: list = field(default_factory=list)
    treatment_current: str = ""
    treatment_past: str = ""
    compliance_med_self: int = 5
    compliance_med_ext: int = 5
    compliance_therapy: int = 5
    investigation_plan: str = ""
    coverage_analysis: str = ""
    uncovered_symptoms: list = field(default_factory=list)

    # Achse II: Biographie & Entwicklung
    education: str = ""
    iq_estimate: str = ""
    developmental_history: str = ""
    formative_experiences: list = field(default_factory=list)
    core_conflicts: list = field(default_factory=list)
    pid5_profile: PID5Profile = field(default_factory=PID5Profile)

    # Achse III: Medizinische Synopse (IIIa-IIIm, symmetrisch zu Achse I)
    med_diagnoses_acute: list = field(default_factory=list)       # IIIa
    med_diagnoses_chronic: list = field(default_factory=list)     # IIIb
    med_diagnoses_contributing: list = field(default_factory=list) # IIIc
    med_diagnoses_remitted: list = field(default_factory=list)    # IIId
    med_remission_factors: list = field(default_factory=list)     # IIIe
    med_treatment_current: str = ""                                # IIIf
    med_treatment_past: str = ""                                   # IIIf
    med_compliance_self: int = 5                                   # IIIg
    med_compliance_ext: int = 5                                    # IIIg
    med_diagnoses_suspected: list = field(default_factory=list)   # IIIh
    med_coverage_analysis: str = ""                                # IIIi
    med_investigation_plan: str = ""                               # IIIj
    medical_conditions: list = field(default_factory=list)        # IIIk (Legacy + Kausalität)
    genetic_factors: str = ""                                      # IIIl
    family_history: str = ""                                       # IIIl
    medications: list = field(default_factory=list)               # IIIm

    # HiTOP-Profil (berechnet aus Cross-Cutting)
    hitop_profile: HiTOPProfile = field(default_factory=HiTOPProfile)

    # Achse IV: Umwelt & Funktion
    functioning: FunctioningAssessment = field(default_factory=FunctioningAssessment)
    contact_persons: list = field(default_factory=list)
    icf_codes: list = field(default_factory=list)

    # Achse V: Bedingungsmodell
    condition_model: ConditionModel = field(default_factory=ConditionModel)
    # Achse V: Strukturierte Faktoren (Sprint 2)
    structured_predisposing: list = field(default_factory=list)
    structured_precipitating: list = field(default_factory=list)
    structured_perpetuating: list = field(default_factory=list)
    structured_protective: list = field(default_factory=list)
    pathophysiological_model: PathophysiologicalModel = field(default_factory=PathophysiologicalModel)

    # Therapieresistenz (Sprint 2)
    treatment_attempts: list = field(default_factory=list)

    # CGI-Verlauf (Sprint 2)
    cgi_assessments: list = field(default_factory=list)

    # Achse VI: Belegsammlung
    evidence_entries: list = field(default_factory=list)
    contact_log: list = field(default_factory=list)

    # CAVE-Warnhinweise (aus FALLBEZOGENE_AUSWERTUNG-Konzept)
    cave_alerts: list = field(default_factory=list)

    # Strukturierte Symptomabdeckung (aus SYNOPSE_VALIDIERT-Konzept)
    symptom_coverage: list = field(default_factory=list)

    # Priorisierter Untersuchungsplan (aus FALLBEZOGENE_AUSWERTUNG-Konzept)
    investigation_plans: list = field(default_factory=list)

    # Longitudinaler Symptomverlauf (aus SYNOPSE_VALIDIERT-Konzept)
    symptom_timeline: list = field(default_factory=list)

    # Screening-Daten
    crosscutting_level1: dict = field(default_factory=dict)
    crosscutting_triggered: list = field(default_factory=list)
    screening_results: dict = field(default_factory=dict)

    # Gatekeeper-Status
    current_gate: int = 0
    gate_results: dict = field(default_factory=dict)


# ===================================================================
# TRANSLATED DATA FUNCTIONS
# ===================================================================

def get_crosscutting_domains():
    """Return cross-cutting symptom domains with translated strings."""
    return {
        "depression": {
            "label": t("cc_depression_label"),
            "items": [t("cc_depression_item_0"), t("cc_depression_item_1")],
            "threshold": 2,
            "level2_instrument": t("cc_depression_level2")
        },
        "anger": {
            "label": t("cc_anger_label"),
            "items": [t("cc_anger_item_0")],
            "threshold": 2,
            "level2_instrument": t("cc_anger_level2")
        },
        "mania": {
            "label": t("cc_mania_label"),
            "items": [t("cc_mania_item_0"), t("cc_mania_item_1")],
            "threshold": 2,
            "level2_instrument": t("cc_mania_level2")
        },
        "anxiety": {
            "label": t("cc_anxiety_label"),
            "items": [t("cc_anxiety_item_0"), t("cc_anxiety_item_1"), t("cc_anxiety_item_2")],
            "threshold": 2,
            "level2_instrument": t("cc_anxiety_level2")
        },
        "somatic": {
            "label": t("cc_somatic_label"),
            "items": [t("cc_somatic_item_0"), t("cc_somatic_item_1")],
            "threshold": 2,
            "level2_instrument": t("cc_somatic_level2")
        },
        "suicidality": {
            "label": t("cc_suicidality_label"),
            "items": [t("cc_suicidality_item_0")],
            "threshold": 1,
            "level2_instrument": t("cc_suicidality_level2")
        },
        "psychosis": {
            "label": t("cc_psychosis_label"),
            "items": [t("cc_psychosis_item_0"), t("cc_psychosis_item_1")],
            "threshold": 1,
            "level2_instrument": t("cc_psychosis_level2")
        },
        "sleep": {
            "label": t("cc_sleep_label"),
            "items": [t("cc_sleep_item_0")],
            "threshold": 2,
            "level2_instrument": t("cc_sleep_level2")
        },
        "memory": {
            "label": t("cc_memory_label"),
            "items": [t("cc_memory_item_0")],
            "threshold": 2,
            "level2_instrument": t("cc_memory_level2")
        },
        "repetitive": {
            "label": t("cc_repetitive_label"),
            "items": [t("cc_repetitive_item_0"), t("cc_repetitive_item_1")],
            "threshold": 2,
            "level2_instrument": t("cc_repetitive_level2")
        },
        "dissociation": {
            "label": t("cc_dissociation_label"),
            "items": [t("cc_dissociation_item_0")],
            "threshold": 2,
            "level2_instrument": t("cc_dissociation_level2")
        },
        "personality": {
            "label": t("cc_personality_label"),
            "items": [t("cc_personality_item_0"), t("cc_personality_item_1")],
            "threshold": 2,
            "level2_instrument": t("cc_personality_level2")
        },
        "substance": {
            "label": t("cc_substance_label"),
            "items": [t("cc_substance_item_0"), t("cc_substance_item_1"), t("cc_substance_item_2")],
            "threshold": 1,
            "level2_instrument": t("cc_substance_level2")
        }
    }


def get_likert_options():
    """Return translated Likert scale options."""
    return {
        0: t("likert_0"),
        1: t("likert_1"),
        2: t("likert_2"),
        3: t("likert_3"),
        4: t("likert_4")
    }


def get_pid5_domains():
    """Return PID-5 domains with translated strings."""
    return {
        "negative_affectivity": {
            "label": t("pid5_negative_affectivity_label"),
            "items": [t(f"pid5_negative_affectivity_item_{i}") for i in range(6)],
            "icd11_trait": t("pid5_negative_affectivity_trait")
        },
        "detachment": {
            "label": t("pid5_detachment_label"),
            "items": [t(f"pid5_detachment_item_{i}") for i in range(6)],
            "icd11_trait": t("pid5_detachment_trait")
        },
        "antagonism": {
            "label": t("pid5_antagonism_label"),
            "items": [t(f"pid5_antagonism_item_{i}") for i in range(6)],
            "icd11_trait": t("pid5_antagonism_trait")
        },
        "disinhibition": {
            "label": t("pid5_disinhibition_label"),
            "items": [t(f"pid5_disinhibition_item_{i}") for i in range(6)],
            "icd11_trait": t("pid5_disinhibition_trait")
        },
        "psychoticism": {
            "label": t("pid5_psychoticism_label"),
            "items": [t(f"pid5_psychoticism_item_{i}") for i in range(6)],
            "icd11_trait": t("pid5_psychoticism_trait")
        },
        "anankastia": {
            "label": t("pid5_anankastia_label"),
            "items": [t(f"pid5_anankastia_item_{i}") for i in range(6)],
            "icd11_trait": t("pid5_anankastia_trait")
        }
    }


def get_gatekeeper_steps():
    """Return gatekeeper steps with translated strings."""
    steps = []
    for i in range(8):
        steps.append({
            "id": i,
            "name": t(f"gate{i}_name"),
            "label": t(f"gate{i}_label"),
            "description": t(f"gate{i}_desc")
        })
    return steps


def get_whodas_items():
    """Return WHODAS 2.0 items with translated strings."""
    return [
        {"domain": t(f"whodas_item_{i}_domain"), "item": t(f"whodas_item_{i}_text")}
        for i in range(12)
    ]


def get_whodas_scale():
    """Return translated WHODAS scale."""
    return {i: t(f"whodas_scale_{i}") for i in range(5)}


def get_stressors():
    """Return translated psychosocial stressors list."""
    return [t(f"stressor_{i}") for i in range(12)]


def get_substances():
    """Return translated substance list."""
    return [
        t("gate2_substance_none"), t("gate2_substance_alcohol"),
        t("gate2_substance_cannabis"), t("gate2_substance_opioids"),
        t("gate2_substance_stimulants"), t("gate2_substance_sedatives"),
        t("gate2_substance_hallucinogens"), t("gate2_substance_inhalants"),
        t("gate2_substance_tobacco"), t("gate2_substance_caffeine"),
        t("gate2_substance_other")
    ]


def get_remission_factors():
    """Return translated remission factors list."""
    return [
        t("ax1_rem_factor_unknown"), t("ax1_rem_factor_time"),
        t("ax1_rem_factor_coping"), t("ax1_rem_factor_support"),
        t("ax1_rem_factor_therapy"), t("ax1_rem_factor_medication"),
        t("ax1_rem_factor_lifestyle"), t("ax1_rem_factor_spontaneous")
    ]


def compute_hitop_profile(crosscutting_level1: dict, crosscutting_domains: dict) -> HiTOPProfile:
    """Compute HiTOP spectrum scores from Cross-Cutting Level 1 data.

    Mapping (Kotov et al., 2017):
      Internalizing = max(Depression, Anxiety, Somatic, Sleep)
      Thought Disorder = max(Psychosis, Dissociation)
      Disinhibited Externalizing = max(Substance, Mania)
      Antagonistic Externalizing = max(Anger)
      Detachment = max(Memory [proxy for withdrawal])
      Somatoform = max(Somatic)
    """
    def domain_max(domain_key):
        items = crosscutting_domains.get(domain_key, {}).get("items", [])
        vals = [crosscutting_level1.get(f"{domain_key}_{i}", 0)
                for i in range(len(items))]
        return max(vals) if vals else 0

    return HiTOPProfile(
        internalizing=max(domain_max("depression"), domain_max("anxiety"),
                          domain_max("somatic"), domain_max("sleep")),
        thought_disorder=max(domain_max("psychosis"), domain_max("dissociation")),
        disinhibited_externalizing=max(domain_max("substance"), domain_max("mania")),
        antagonistic_externalizing=domain_max("anger"),
        detachment=domain_max("memory"),
        somatoform=domain_max("somatic"),
    )


def render_hitop_radar(hitop: HiTOPProfile):
    """Render HiTOP spectrum radar chart using Plotly."""
    if not HAS_PLOTLY:
        return
    categories = [
        t("hitop_internalizing"),
        t("hitop_thought_disorder"),
        t("hitop_disinhibited_ext"),
        t("hitop_antagonistic_ext"),
        t("hitop_detachment"),
        t("hitop_somatoform"),
    ]
    values = [
        hitop.internalizing,
        hitop.thought_disorder,
        hitop.disinhibited_externalizing,
        hitop.antagonistic_externalizing,
        hitop.detachment,
        hitop.somatoform,
    ]
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure(data=go.Scatterpolar(
        r=values_closed, theta=categories_closed,
        fill='toself', line_color='#dc322f',
        name='HiTOP'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 4])),
        showlegend=False, height=400,
        title=t("hitop_title")
    )
    st.plotly_chart(fig, use_container_width=True)


# ===================================================================
# STREAMLIT-ANWENDUNG
# ===================================================================

st.set_page_config(
    page_title="Multiaxiales Diagnostik-Expertensystem v10",
    page_icon="🏥",
    layout="wide"
)

# ---------------------------------------------------------------------------
# First-start acknowledgement gate (MDR-Abgrenzung).
# Blocks the app until the user has confirmed the four mandatory items.
# Implementation: see disclaimer_streamlit.py / disclaimer_core.py.
# ---------------------------------------------------------------------------
try:
    from disclaimer_streamlit import require_disclaimer_acceptance
    require_disclaimer_acceptance()
except ImportError:
    # If the disclaimer module is missing we fail closed: show a warning
    # but let the app continue so tests can run. The README banner still
    # applies.
    st.error(
        "Disclaimer module not found. The legal notice in README.md "
        "and NOTICE still applies. / Disclaimer-Modul fehlt."
    )

st.markdown("""
<style>
    .axis-header {
        background-color: #002b36;
        color: #93a1a1;
        padding: 12px 16px;
        border-radius: 5px;
        font-weight: bold;
        margin: 20px 0 10px 0;
        font-size: 1.1em;
    }
    .gate-active { color: #268bd2; font-weight: bold; }
    .gate-done { color: #859900; }
    .gate-locked { color: #586e75; }
    .status-alert { padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
    .suspected { background-color: #fdf6e3; border-left: 4px solid #b58900; }
    .excluded { background-color: #eee8d5; border-left: 4px solid #586e75; }
    .critical { background-color: #fdf6e3; border-left: 4px solid #dc322f; }
    .coverage-gap { background-color: #fce4e4; border-left: 4px solid #dc322f;
                    padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)


# --- Session State Initialisierung ---
if 'patient' not in st.session_state:
    st.session_state.patient = PatientData()

if 'current_gate' not in st.session_state:
    st.session_state.current_gate = 0

if 'lang' not in st.session_state:
    st.session_state.lang = "de"

# Auto-load session on first start (BEFORE page render)
if 'session_autoloaded' not in st.session_state:
    _auto_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "diagnostic_session.json")
    if os.path.exists(_auto_path):
        try:
            with open(_auto_path, "r", encoding="utf-8") as _f_auto:
                _auto_data = json.load(_f_auto)
            _pd_dict = _auto_data.get("patient", {})
            if "pid5_profile" in _pd_dict:
                _pd_dict["pid5_profile"] = PID5Profile(**_pd_dict["pid5_profile"])
            if "hitop_profile" in _pd_dict:
                _pd_dict["hitop_profile"] = HiTOPProfile(**_pd_dict["hitop_profile"])
            if "functioning" in _pd_dict:
                _pd_dict["functioning"] = FunctioningAssessment(**_pd_dict["functioning"])
            if "condition_model" in _pd_dict:
                _pd_dict["condition_model"] = ConditionModel(**_pd_dict["condition_model"])
            if "pathophysiological_model" in _pd_dict:
                _pd_dict["pathophysiological_model"] = PathophysiologicalModel(
                    **_pd_dict["pathophysiological_model"])
            _valid_fields = {f.name for f in PatientData.__dataclass_fields__.values()}
            _filtered = {k: v for k, v in _pd_dict.items() if k in _valid_fields}
            st.session_state.patient = PatientData(**_filtered)
            st.session_state.current_gate = _auto_data.get("current_gate", 0)
            st.session_state.lang = _auto_data.get("lang", "de")
        except Exception:
            pass  # Silently fall back to empty session
    st.session_state.session_autoloaded = True


def get_patient() -> PatientData:
    return st.session_state.patient


# ===================================================================
# SIDEBAR: Language, Navigation & Gatekeeper-Status
# ===================================================================

st.sidebar.title(t("sidebar_title"))
st.sidebar.markdown("---")

# Language Selector
lang_options = ["Deutsch", "English"]
lang_index = 0 if st.session_state.lang == "de" else 1
lang_choice = st.sidebar.selectbox(
    "🌐 Sprache / Language",
    lang_options,
    index=lang_index,
    key="lang_select"
)
st.session_state.lang = "de" if lang_choice == "Deutsch" else "en"

st.sidebar.markdown("---")

# Gatekeeper-Fortschritt
st.sidebar.subheader(t("gatekeeper_progress"))
gatekeeper_steps = get_gatekeeper_steps()
for step in gatekeeper_steps:
    idx = step["id"]
    if idx < st.session_state.current_gate:
        st.sidebar.markdown(f"<span class='gate-done'>✅ {step['label']}</span>",
                            unsafe_allow_html=True)
    elif idx == st.session_state.current_gate:
        st.sidebar.markdown(f"<span class='gate-active'>🔄 {step['label']}</span>",
                            unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<span class='gate-locked'>🔒 {step['label']}</span>",
                            unsafe_allow_html=True)

st.sidebar.markdown("---")

# Achsen-Navigation
nav_options = [
    t("nav_gatekeeper"),
    t("nav_axis1"),
    t("nav_axis2"),
    t("nav_axis3"),
    t("nav_axis4"),
    t("nav_axis5"),
    t("nav_axis6"),
    t("nav_synopsis")
]
menu = st.sidebar.radio(t("nav_label"), nav_options)


# ===================================================================
# GATEKEEPER-PROZESS
# ===================================================================

if menu == t("nav_gatekeeper"):
    st.markdown(f"<div class='axis-header'>{t('header_gatekeeper')}</div>",
                unsafe_allow_html=True)

    current = st.session_state.current_gate
    steps = get_gatekeeper_steps()
    if current < len(steps):
        step = steps[current]
        st.info(f"**{step['label']}**\n\n{step['description']}")

    # --- Stufe 0: Intake ---
    if current == 0:
        st.subheader(t("intake_subheader"))
        p = get_patient()
        with st.form("intake_form"):
            col1, col2 = st.columns(2)
            intake_name = col1.text_input(t("intake_name"),
                                          value=p.patient_name, key="intake_name")
            intake_dob = col2.date_input(t("intake_dob"), key="intake_dob",
                            value=datetime.date(1990, 1, 1))
            intake_reason = st.text_area(t("intake_reason"),
                                         value=p.presenting_complaint, key="intake_reason")
            if st.form_submit_button(t("intake_submit")):
                p.patient_name = intake_name
                p.patient_dob = str(intake_dob)
                p.presenting_complaint = intake_reason
                st.session_state.current_gate = 1
                st.rerun()

    # --- Stufe 1: Simulationsausschluss ---
    elif current == 1:
        st.subheader(t("gate1_subheader"))
        with st.form("gate1_form"):
            st.write(t("gate1_evaluate"))
            g1_1 = st.selectbox(t("gate1_inconsistency"),
                                [t("gate1_inconsistency_0"), t("gate1_inconsistency_1"),
                                 t("gate1_inconsistency_2"), t("gate1_inconsistency_3")],
                                key="g1_inconsistency")
            g1_2 = st.selectbox(t("gate1_incentive"),
                                [t("gate1_incentive_0"), t("gate1_incentive_1"),
                                 t("gate1_incentive_2"), t("gate1_incentive_3")],
                                key="g1_incentive")
            g1_3 = st.selectbox(t("gate1_cooperation"),
                                [t("gate1_cooperation_0"), t("gate1_cooperation_1"),
                                 t("gate1_cooperation_2")],
                                key="g1_cooperation")
            g1_note = st.text_area(t("gate1_notes"), key="g1_notes")

            if st.form_submit_button(t("gate1_submit")):
                p = get_patient()
                p.gate_results["step1_malingering"] = {
                    "inconsistency": g1_1,
                    "incentive": g1_2,
                    "cooperation": g1_3,
                    "notes": g1_note,
                    "passed": g1_1 != t("gate1_inconsistency_3") and g1_2 != t("gate1_incentive_3")
                }
                if g1_1 == t("gate1_inconsistency_3") or g1_2 == t("gate1_incentive_3"):
                    st.warning(t("gate1_warning"))
                st.session_state.current_gate = 2
                st.rerun()

    # --- Stufe 2: Substanzausschluss ---
    elif current == 2:
        st.subheader(t("gate2_subheader"))
        with st.form("gate2_form"):
            g2_substances = st.multiselect(
                t("gate2_substances_label"),
                get_substances()
            )
            g2_temporal = st.selectbox(
                t("gate2_temporal"),
                [t("gate2_temporal_0"), t("gate2_temporal_1"),
                 t("gate2_temporal_2"), t("gate2_temporal_3")]
            )
            g2_history = st.text_area(t("gate2_history"))

            if st.form_submit_button(t("gate2_submit")):
                p = get_patient()
                p.gate_results["step2_substance"] = {
                    "substances": g2_substances,
                    "temporal_relation": g2_temporal,
                    "history": g2_history,
                    "substance_induced": g2_temporal == t("gate2_temporal_3")
                }
                st.session_state.current_gate = 3
                st.rerun()

    # --- Stufe 3: Medizinischer Ausschluss ---
    elif current == 3:
        st.subheader(t("gate3_subheader"))
        with st.form("gate3_form"):
            g3_conditions = st.text_area(t("gate3_conditions"))
            g3_causality = st.selectbox(
                t("gate3_causality"),
                [t("gate3_causality_0"), t("gate3_causality_1"), t("gate3_causality_2")]
            )
            g3_labs = st.text_area(t("gate3_labs"))

            if st.form_submit_button(t("gate3_submit")):
                p = get_patient()
                p.gate_results["step3_medical"] = {
                    "conditions": g3_conditions,
                    "causality": g3_causality,
                    "labs": g3_labs,
                    "fully_explained": g3_causality == t("gate3_causality_2")
                }
                st.session_state.current_gate = 4
                st.rerun()

    # --- Stufe 4: Cross-Cutting Screening ---
    elif current == 4:
        st.subheader(t("gate4_subheader"))
        st.write(t("gate4_instruction"))

        crosscutting_domains = get_crosscutting_domains()
        likert_options = get_likert_options()

        with st.form("crosscutting_form"):
            responses = {}
            for domain_key, domain in crosscutting_domains.items():
                st.markdown(f"**{domain['label']}** "
                            f"({t('gate4_threshold')}: ≥{domain['threshold']})")
                for i, item_text in enumerate(domain["items"]):
                    val = st.select_slider(
                        item_text,
                        options=list(likert_options.values()),
                        key=f"cc_{domain_key}_{i}"
                    )
                    # Extrahiere numerischen Wert (robust: Fallback auf Index)
                    try:
                        num_val = int(val.split("(")[1].replace(")", ""))
                    except (IndexError, ValueError):
                        num_val = list(likert_options.values()).index(val) if val in likert_options.values() else 0
                    responses[f"{domain_key}_{i}"] = num_val
                st.markdown("---")

            if st.form_submit_button(t("gate4_submit")):
                p = get_patient()
                p.crosscutting_level1 = responses

                # Schwellenlogik
                triggered = []
                for domain_key, domain in crosscutting_domains.items():
                    domain_max = 0
                    for i in range(len(domain["items"])):
                        val = responses.get(f"{domain_key}_{i}", 0)
                        domain_max = max(domain_max, val)
                    if domain_max >= domain["threshold"]:
                        triggered.append({
                            "domain": domain_key,
                            "label": domain["label"],
                            "max_score": domain_max,
                            "threshold": domain["threshold"],
                            "level2": domain["level2_instrument"]
                        })

                p.crosscutting_triggered = triggered

                # HiTOP-Spektren berechnen
                p.hitop_profile = compute_hitop_profile(
                    responses, crosscutting_domains)

                st.session_state.current_gate = 5
                st.rerun()

    # --- Stufe 5: Störungsspezifische Module ---
    elif current == 5:
        st.subheader(t("gate5_subheader"))
        p = get_patient()

        # Testcenter URL (konfigurierbar)
        _TESTCENTER_URL = os.environ.get(
            "TESTCENTER_URL", "http://localhost:5050")

        # Mapping: Cross-Cutting Domain → Testcenter Test-IDs
        _DOMAIN_TO_TESTS = {
            "depression": [("phq9", "PHQ-9")],
            "anxiety": [("gad7", "GAD-7")],
            "somatic": [("sss8", "SSS-8")],
            "suicidality": [("cssrs", "C-SSRS")],
            "psychosis": [("pq16", "PQ-16")],
            "sleep": [("isi", "ISI")],
            "repetitive": [("ocir", "OCI-R")],
            "dissociation": [("des2", "DES-II")],
            "personality": [("pid5bf", "PID-5-BF")],
            "substance": [("audit", "AUDIT")],
        }

        if p.crosscutting_triggered:
            st.write(f"**{t('gate5_triggered')}**")
            for tr in p.crosscutting_triggered:
                safety = t("gate5_safety_critical") if tr["threshold"] == 1 and tr["max_score"] >= 1 else ""
                # Build testcenter links for this domain
                tc_links = ""
                domain_tests = _DOMAIN_TO_TESTS.get(tr["domain"], [])
                if domain_tests:
                    links_html = " | ".join(
                        f"<a href='{esc(_TESTCENTER_URL)}/tests/{tid}' "
                        f"target='_blank' style='color:#1565C0;font-weight:bold;'>"
                        f"&#x1F4CB; {name}</a>"
                        for tid, name in domain_tests
                    )
                    tc_links = (
                        f"<div style='margin-top:4px;padding:4px 8px;"
                        f"background:#e3f2fd;border-radius:4px;'>"
                        f"Testcenter: {links_html}</div>"
                    )
                st.markdown(
                    f"<div class='status-alert {'critical' if safety else 'suspected'}'>"
                    f"<b>{esc(tr['label'])}</b>: {t('gate5_max_score')} {tr['max_score']} "
                    f"({t('gate4_threshold')} ≥{tr['threshold']}){esc(safety)}<br/>"
                    f"→ Level 2: {esc(tr['level2'])}"
                    f"{tc_links}</div>",
                    unsafe_allow_html=True
                )

            # Testcenter-Schnellzugriff
            st.markdown("---")
            _lang = st.session_state.get("lang", "de")
            _tc_label = ("Open Testcenter" if _lang == "en"
                         else "Testcenter öffnen")
            _tc_new = ("Create Test Session" if _lang == "en"
                       else "Testsitzung erstellen")
            col_tc1, col_tc2 = st.columns(2)
            col_tc1.markdown(
                f"<a href='{esc(_TESTCENTER_URL)}/tests?lang={_lang}' "
                f"target='_blank' style='display:inline-block;padding:8px 16px;"
                f"background:#1565C0;color:white;border-radius:4px;"
                f"text-decoration:none;'>{_tc_label}</a>",
                unsafe_allow_html=True
            )
            col_tc2.markdown(
                f"<a href='{esc(_TESTCENTER_URL)}/sessions/create?lang={_lang}' "
                f"target='_blank' style='display:inline-block;padding:8px 16px;"
                f"background:#2E7D32;color:white;border-radius:4px;"
                f"text-decoration:none;'>{_tc_new}</a>",
                unsafe_allow_html=True
            )
        else:
            st.success(t("gate5_no_trigger"))

        # --- Testcenter-Ergebnisse importieren ---
        st.markdown("---")
        _imp_label = ("Import Testcenter Results" if _lang == "en"
                      else "Testcenter-Ergebnisse importieren")
        with st.expander(_imp_label):
            _imp_help = (
                "Enter a session token or battery ID from the Testcenter to import scores."
                if _lang == "en" else
                "Geben Sie einen Sitzungs-Token oder Paket-ID aus dem Testcenter ein, "
                "um Ergebnisse zu importieren."
            )
            st.caption(_imp_help)
            _imp_token = st.text_input(
                "Token / Battery-ID",
                key="tc_import_token",
                placeholder="z.B. a8f3b21c-6f0"
            )
            if st.button(
                "Import" if _lang == "en" else "Importieren",
                key="tc_import_btn"
            ):
                if _imp_token:
                    import urllib.request
                    _imported = []
                    _errors = []

                    # Try as single session first
                    _urls = [
                        f"{_TESTCENTER_URL}/api/results/{_imp_token}",
                    ]

                    for _url in _urls:
                        try:
                            _req = urllib.request.urlopen(_url, timeout=5)
                            _data = json.loads(_req.read().decode("utf-8"))

                            if _data.get("status") == "completed" and _data.get("scores"):
                                _tid = _data["test_id"]
                                _scores = _data["scores"]
                                p.screening_results[_tid] = {
                                    "token": _data.get("token", _imp_token),
                                    "test_id": _tid,
                                    "test_name": _scores.get("test_name", {}),
                                    "total_score": _scores.get("total_score"),
                                    "max_score": _scores.get("max_score"),
                                    "severity": _scores.get("severity"),
                                    "label": _scores.get("label", {}),
                                    "color": _scores.get("color"),
                                    "subscales": _scores.get("subscales", []),
                                    "alerts": _scores.get("alerts", []),
                                    "imported_at": datetime.datetime.now().isoformat(),
                                }
                                _imported.append(_tid)
                            elif _data.get("status") == "pending":
                                _errors.append(
                                    f"Token {_imp_token}: "
                                    + ("not yet completed" if _lang == "en"
                                       else "noch nicht abgeschlossen")
                                )
                            break  # Single session found
                        except Exception:
                            pass  # Try next URL or battery

                    # If single session didn't work, try as battery
                    if not _imported and not _errors:
                        try:
                            _bat_url = f"{_TESTCENTER_URL}/api/batteries/{_imp_token}"
                            _req = urllib.request.urlopen(_bat_url, timeout=5)
                            _bat_data = json.loads(_req.read().decode("utf-8"))
                            # Battery API might not exist yet, fallback:
                        except Exception:
                            pass

                    # If still nothing, try listing sessions by scanning
                    if not _imported and not _errors:
                        _errors.append(
                            f"Token '{_imp_token}': "
                            + ("not found or Testcenter not reachable"
                               if _lang == "en"
                               else "nicht gefunden oder Testcenter nicht erreichbar")
                        )

                    if _imported:
                        st.success(
                            ("Imported: " if _lang == "en" else "Importiert: ")
                            + ", ".join(_imported)
                        )
                        st.rerun()
                    for _e in _errors:
                        st.error(_e)

        # Importierte Ergebnisse anzeigen
        if p.screening_results:
            _sr_label = ("Imported Screening Results" if _lang == "en"
                         else "Importierte Screening-Ergebnisse")
            st.subheader(_sr_label)
            _sr_cols = st.columns(min(len(p.screening_results), 4))
            for _idx, (_tid, _sr) in enumerate(p.screening_results.items()):
                with _sr_cols[_idx % len(_sr_cols)]:
                    _name = _sr.get("test_name", {})
                    _disp_name = (_name.get(_lang, _name.get("de", _tid))
                                  if isinstance(_name, dict) else str(_name))
                    st.metric(
                        label=_tid.upper(),
                        value=f"{_sr.get('total_score', '?')} / {_sr.get('max_score', '?')}",
                        help=_disp_name
                    )
                    _sev_label = _sr.get("label", {})
                    if isinstance(_sev_label, dict):
                        _sev_label = _sev_label.get(_lang, _sev_label.get("de", ""))
                    _color = _sr.get("color", "#999")
                    st.markdown(
                        f"<span style='color:{esc(_color)};font-weight:bold;'>"
                        f"{esc(str(_sev_label))}</span>",
                        unsafe_allow_html=True
                    )
                    if _sr.get("alerts"):
                        for _al in _sr["alerts"]:
                            _al_text = (_al.get(_lang, _al.get("de", str(_al)))
                                        if isinstance(_al, dict) else str(_al))
                            st.error(_al_text)

        # HiTOP-Spektren-Radar anzeigen
        if p.crosscutting_level1:
            st.markdown("---")
            st.subheader(t("hitop_title"))
            st.caption(t("hitop_info"))
            render_hitop_radar(p.hitop_profile)
        else:
            st.info(t("hitop_no_data"))

        st.markdown("---")
        st.write(f"**{t('gate5_diag_assessment')}**")

        with st.form("disorder_module_form"):
            diag_name = st.text_input(t("gate5_diag_name"))
            _lang = st.session_state.get("lang", "de")
            col1, col2 = st.columns(2)
            if HAS_CODE_DB:
                _icd11_opts = [""] + _load_code_options("icd11", _lang)
                _dsm5_opts = [""] + _load_code_options("dsm5", _lang)
                diag_icd11_sel = col1.selectbox(
                    t("gate5_icd11_code"), _icd11_opts, key="g5_icd11")
                diag_dsm5_sel = col2.selectbox(
                    t("gate5_dsm5_code"), _dsm5_opts, key="g5_dsm5")
                col_m1, col_m2 = st.columns(2)
                diag_icd11_manual = col_m1.text_input(
                    t("code_manual_icd11"), key="g5_icd11_man")
                diag_dsm5_manual = col_m2.text_input(
                    t("code_manual_dsm5"), key="g5_dsm5_man")
            else:
                diag_icd11_sel = ""
                diag_dsm5_sel = ""
                diag_icd11_manual = col1.text_input(t("gate5_icd11_code"))
                diag_dsm5_manual = col2.text_input(t("gate5_dsm5_code"))
            status_options = [t("gate5_status_acute"), t("gate5_status_chronic"),
                              t("gate5_status_suspected"), t("gate5_status_excluded")]
            diag_status = st.selectbox(t("gate5_status"), status_options)

            # NEU: Konfidenz & Severity (inspiriert durch FALLBEZOGENE_AUSWERTUNG)
            col_c, col_s = st.columns(2)
            diag_confidence = col_c.slider(
                t("diag_confidence"), 0, 100, 50,
                help=t("diag_confidence_help"))
            severity_options = [t("diag_severity_low"), t("diag_severity_medium"),
                                t("diag_severity_high"), t("diag_severity_very_high")]
            diag_severity = col_s.selectbox(t("diag_severity"), severity_options)

            diag_evidence = st.text_area(t("gate5_evidence"))

            # NEU: PRO/CONTRA-Evidenzbewertung
            col_pro, col_con = st.columns(2)
            diag_pro = col_pro.text_area(t("diag_pro_evidence"), height=80)
            diag_contra = col_con.text_area(t("diag_contra_evidence"), height=80)

            if st.form_submit_button(t("gate5_add_diag")):
                # Code aus Selectbox oder manuellem Feld extrahieren
                diag_icd11 = _extract_code(diag_icd11_sel) if diag_icd11_sel else diag_icd11_manual.strip()
                diag_dsm5 = _extract_code(diag_dsm5_sel) if diag_dsm5_sel else diag_dsm5_manual.strip()
                # Auto-Cross-Mapping: DSM-5 → ICD-11 und umgekehrt
                if diag_dsm5 and not diag_icd11:
                    diag_icd11 = get_cross_mapped_code("dsm5", diag_dsm5, "icd11")
                elif diag_icd11 and not diag_dsm5:
                    diag_dsm5 = get_cross_mapped_code("icd11", diag_icd11, "dsm5")
                # Auto-Name aus Code-Titel wenn leer
                if not diag_name.strip() and diag_icd11:
                    diag_name = get_code_title("icd11", diag_icd11, _lang)
                elif not diag_name.strip() and diag_dsm5:
                    diag_name = get_code_title("dsm5", diag_dsm5, _lang)
                diag = Diagnosis(
                    code_icd11=diag_icd11,
                    code_dsm5=diag_dsm5,
                    name=diag_name,
                    status=diag_status.lower(),
                    evidence=diag_evidence,
                    confidence_pct=diag_confidence,
                    severity=diag_severity,
                    evidence_pro=diag_pro,
                    evidence_contra=diag_contra
                )
                if diag_status == t("gate5_status_acute"):
                    p.diagnoses_acute.append(asdict(diag))
                elif diag_status == t("gate5_status_chronic"):
                    p.diagnoses_chronic.append(asdict(diag))
                elif diag_status == t("gate5_status_suspected"):
                    p.diagnoses_suspected.append(asdict(diag))
                elif diag_status == t("gate5_status_excluded"):
                    p.diagnoses_excluded.append(asdict(diag))
                st.rerun()

        # Aktuelle Diagnosen anzeigen
        all_diags = (p.diagnoses_acute + p.diagnoses_chronic +
                     p.diagnoses_suspected + p.diagnoses_excluded)
        if all_diags and HAS_PANDAS:
            df = pd.DataFrame(all_diags)[["name", "code_icd11", "code_dsm5", "status"]]
            st.table(df)

        if st.button(t("gate5_to_gate6")):
            st.session_state.current_gate = 6
            st.rerun()

    # --- Stufe 6: Funktionsniveau ---
    elif current == 6:
        st.subheader(t("gate6_subheader"))
        p = get_patient()

        tab_gaf, tab_whodas, tab_gdb = st.tabs(["GAF", "WHODAS 2.0", "GdB"])

        with tab_gaf:
            st.warning(t("gaf_deprecated_notice"))
            p.functioning.gaf_score = st.slider(
                t("gate6_gaf_label"),
                min_value=0, max_value=100, value=p.functioning.gaf_score,
                help=t("gate6_gaf_help")
            )
            st.caption(t("gate6_gaf_note"))

        with tab_whodas:
            st.write(f"**{t('gate6_whodas_title')}**")
            st.write(t("gate6_whodas_instruction"))
            whodas_items = get_whodas_items()
            whodas_scale = get_whodas_scale()
            with st.form("whodas_form"):
                whodas_scores = []
                for i, item in enumerate(whodas_items):
                    val = st.select_slider(
                        f"[{item['domain']}] {item['item']}",
                        options=list(whodas_scale.values()),
                        key=f"whodas_{i}"
                    )
                    num = list(whodas_scale.values()).index(val)
                    whodas_scores.append(num)

                if st.form_submit_button(t("gate6_whodas_submit")):
                    total = sum(whodas_scores)
                    max_score = len(whodas_items) * 4
                    pct = (total / max_score) * 100
                    st.metric(t("gate6_whodas_total"),
                              f"{total}/{max_score} ({pct:.0f}%)")
                    # WHODAS domain scores in PatientData speichern
                    # Items 0-1: Cognition, 2-3: Mobility, 4-5: Self-care,
                    # 6-7: Getting along, 8-9: Life activities, 10-11: Participation
                    if len(whodas_scores) >= 12:
                        p.functioning.whodas_cognition = whodas_scores[0] + whodas_scores[1]
                        p.functioning.whodas_mobility = whodas_scores[2] + whodas_scores[3]
                        p.functioning.whodas_selfcare = whodas_scores[4] + whodas_scores[5]
                        p.functioning.whodas_getting_along = whodas_scores[6] + whodas_scores[7]
                        p.functioning.whodas_life_activities = whodas_scores[8] + whodas_scores[9]
                        p.functioning.whodas_participation = whodas_scores[10] + whodas_scores[11]

        with tab_gdb:
            p.functioning.gdb_score = st.slider(
                t("gate6_gdb_label"),
                min_value=0, max_value=100, step=10,
                value=p.functioning.gdb_score,
                help=t("gate6_gdb_help")
            )
            if p.functioning.gdb_score >= 50:
                st.warning(f"{t('gate6_gdb_warning')} (GdB {p.functioning.gdb_score})")

        st.markdown("---")
        st.write(f"**{t('gate6_stressors_label')}**")
        _g6_stressor_opts = get_stressors()
        _g6_valid_defaults = [s for s in p.functioning.psychosocial_stressors if s in _g6_stressor_opts]
        stressors = st.multiselect(
            t("gate6_stressors_select"),
            _g6_stressor_opts,
            default=_g6_valid_defaults
        )
        p.functioning.psychosocial_stressors = stressors

        if st.button(t("gate6_to_synopsis")):
            st.session_state.current_gate = 7
            st.rerun()

    # --- Stufe 7: Synopse ---
    elif current >= 7:
        st.subheader(t("gate7_complete"))
        st.success(t("gate7_success"))
        if st.button(t("gate7_reset")):
            st.session_state.current_gate = 0
            st.rerun()


# ===================================================================
# ACHSE I: PSYCHISCHE PROFILE (ERWEITERT)
# ===================================================================

elif menu == t("nav_axis1"):
    st.markdown(f"<div class='axis-header'>{t('header_axis1')}</div>",
                unsafe_allow_html=True)
    p = get_patient()

    tab_diag, tab_rem, tab_treat, tab_plan, tab_therapy_resist = st.tabs([
        t("ax1_tab_diag"),
        t("ax1_tab_rem"),
        t("ax1_tab_treat"),
        t("ax1_tab_plan"),
        t("therapy_resist_subheader")
    ])

    with tab_diag:
        st.subheader(t("ax1_diag_subheader"))
        st.write(f"**{t('ax1_diag_current')}**")
        for d in p.diagnoses_acute:
            st.error(f"🔴 {t('ax1_acute_prefix')}: {d['name']} ({d.get('code_icd11','')}/{d.get('code_dsm5','')})")
        for d in p.diagnoses_chronic:
            st.info(f"🟡 {t('ax1_chronic_prefix')}: {d['name']} ({d.get('code_icd11','')}/{d.get('code_dsm5','')})")

        st.write(f"**{t('ax1_suspected_header')}**")
        for d in p.diagnoses_suspected:
            st.markdown(
                f"<div class='status-alert suspected'>? {t('ax1_suspected_prefix')}: {esc(d['name'])}</div>",
                unsafe_allow_html=True
            )

        st.write(f"**{t('ax1_excluded_header')}**")
        for d in p.diagnoses_excluded:
            st.markdown(
                f"<div class='status-alert excluded'>✖ {t('ax1_excluded_prefix')}: {esc(d['name'])}</div>",
                unsafe_allow_html=True
            )

        # --- Diagnose hinzufügen (auch nach Gatekeeper-Abschluss) ---
        st.markdown("---")
        with st.form("ax1_add_diag_form"):
            ax1_diag_name = st.text_input(t("gate5_diag_name"), key="ax1_diag_name")
            _lang = st.session_state.get("lang", "de")
            col1, col2 = st.columns(2)
            if HAS_CODE_DB:
                _ax1_icd11_opts = [""] + _load_code_options("icd11", _lang)
                _ax1_dsm5_opts = [""] + _load_code_options("dsm5", _lang)
                ax1_icd11_sel = col1.selectbox(
                    t("gate5_icd11_code"), _ax1_icd11_opts, key="ax1_icd11")
                ax1_dsm5_sel = col2.selectbox(
                    t("gate5_dsm5_code"), _ax1_dsm5_opts, key="ax1_dsm5")
                col_m1, col_m2 = st.columns(2)
                ax1_icd11_manual = col_m1.text_input(
                    t("code_manual_icd11"), key="ax1_icd11_man")
                ax1_dsm5_manual = col_m2.text_input(
                    t("code_manual_dsm5"), key="ax1_dsm5_man")
            else:
                ax1_icd11_sel = ""
                ax1_dsm5_sel = ""
                ax1_icd11_manual = col1.text_input(t("gate5_icd11_code"), key="ax1_icd11_man_nb")
                ax1_dsm5_manual = col2.text_input(t("gate5_dsm5_code"), key="ax1_dsm5_man_nb")
            ax1_status_options = [t("gate5_status_acute"), t("gate5_status_chronic"),
                                  t("gate5_status_suspected"), t("gate5_status_excluded")]
            ax1_diag_status = st.selectbox(t("gate5_status"), ax1_status_options, key="ax1_status")

            col_c, col_s = st.columns(2)
            ax1_confidence = col_c.slider(
                t("diag_confidence"), 0, 100, 50, key="ax1_confidence",
                help=t("diag_confidence_help"))
            ax1_severity_options = [t("diag_severity_low"), t("diag_severity_medium"),
                                    t("diag_severity_high"), t("diag_severity_very_high")]
            ax1_severity = col_s.selectbox(t("diag_severity"), ax1_severity_options, key="ax1_severity")

            ax1_evidence = st.text_area(t("gate5_evidence"), key="ax1_evidence")

            col_pro, col_con = st.columns(2)
            ax1_pro = col_pro.text_area(t("diag_pro_evidence"), height=80, key="ax1_pro")
            ax1_contra = col_con.text_area(t("diag_contra_evidence"), height=80, key="ax1_contra")

            if st.form_submit_button(t("gate5_add_diag")):
                ax1_icd11 = _extract_code(ax1_icd11_sel) if ax1_icd11_sel else ax1_icd11_manual.strip()
                ax1_dsm5 = _extract_code(ax1_dsm5_sel) if ax1_dsm5_sel else ax1_dsm5_manual.strip()
                if ax1_dsm5 and not ax1_icd11:
                    ax1_icd11 = get_cross_mapped_code("dsm5", ax1_dsm5, "icd11")
                elif ax1_icd11 and not ax1_dsm5:
                    ax1_dsm5 = get_cross_mapped_code("icd11", ax1_icd11, "dsm5")
                if not ax1_diag_name.strip() and ax1_icd11:
                    ax1_diag_name = get_code_title("icd11", ax1_icd11, _lang)
                elif not ax1_diag_name.strip() and ax1_dsm5:
                    ax1_diag_name = get_code_title("dsm5", ax1_dsm5, _lang)
                ax1_diag = Diagnosis(
                    code_icd11=ax1_icd11,
                    code_dsm5=ax1_dsm5,
                    name=ax1_diag_name,
                    status=ax1_diag_status.lower(),
                    evidence=ax1_evidence,
                    confidence_pct=ax1_confidence,
                    severity=ax1_severity,
                    evidence_pro=ax1_pro,
                    evidence_contra=ax1_contra
                )
                if ax1_diag_status == t("gate5_status_acute"):
                    p.diagnoses_acute.append(asdict(ax1_diag))
                elif ax1_diag_status == t("gate5_status_chronic"):
                    p.diagnoses_chronic.append(asdict(ax1_diag))
                elif ax1_diag_status == t("gate5_status_suspected"):
                    p.diagnoses_suspected.append(asdict(ax1_diag))
                elif ax1_diag_status == t("gate5_status_excluded"):
                    p.diagnoses_excluded.append(asdict(ax1_diag))
                st.rerun()

    with tab_rem:
        st.subheader(t("ax1_rem_subheader"))
        with st.form("remission_form"):
            rem_name = st.text_input(t("ax1_rem_name"))
            rem_factors = st.multiselect(
                t("ax1_rem_factors"),
                get_remission_factors()
            )
            rem_evidence = st.text_area(t("ax1_rem_evidence"))
            if st.form_submit_button(t("ax1_rem_submit")):
                p.diagnoses_remitted.append(asdict(Diagnosis(
                    name=rem_name,
                    status="remittiert",
                    evidence=rem_evidence,
                    remission_factors=rem_factors
                )))
                st.rerun()

        for d in p.diagnoses_remitted:
            factors = ", ".join(d.get("remission_factors", []))
            st.success(f"✅ {t('ax1_rem_prefix')}: {d['name']} ({t('ax1_rem_factors_label')}: {factors})")

    with tab_treat:
        st.subheader(t("ax1_treat_subheader"))
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**{t('ax1_treat_current')}**")
            p.treatment_current = st.text_area(
                t("ax1_treat_current_area"), value=p.treatment_current,
                key="curr_treat_ax1")
        with col2:
            st.write(f"**{t('ax1_treat_past')}**")
            p.treatment_past = st.text_area(
                t("ax1_treat_past_area"), value=p.treatment_past,
                key="past_treat_ax1")

        st.subheader(t("ax1_compliance_subheader"))
        c1, c2, c3 = st.columns(3)
        p.compliance_med_self = c1.slider(t("ax1_compliance_med_self"), 0, 10,
                                          p.compliance_med_self)
        p.compliance_med_ext = c2.slider(t("ax1_compliance_med_ext"), 0, 10,
                                         p.compliance_med_ext)
        p.compliance_therapy = c3.slider(t("ax1_compliance_therapy"), 0, 10,
                                         p.compliance_therapy)

    with tab_plan:
        st.subheader(t("ax1_plan_subheader"))

        # ── Ii: STRUKTURIERTE SYMPTOMABDECKUNG ──
        st.subheader(t("ax1_coverage_subheader"))
        st.info(t("ax1_coverage_info"))

        # Strukturierte Symptom-Diagnosen-Zuordnung (aus SYNOPSE_VALIDIERT)
        st.markdown(f"**{t('coverage_structured_title')}**")
        with st.form("coverage_form"):
            col1, col2, col3 = st.columns([3, 3, 1])
            cov_symptom = col1.text_input(t("coverage_symptom"))
            cov_diag = col2.text_input(t("coverage_explaining_diag"))
            cov_pct = col3.number_input(t("coverage_pct"), 0, 100, 85)
            if st.form_submit_button(t("coverage_add")):
                p.symptom_coverage.append(asdict(SymptomCoverage(
                    symptom=cov_symptom,
                    explaining_diagnoses=cov_diag,
                    coverage_pct=cov_pct
                )))
                st.rerun()

        if p.symptom_coverage:
            if HAS_PANDAS:
                df_cov = pd.DataFrame(p.symptom_coverage)
                st.table(df_cov)
            # Gesamt-Abdeckungsmetrik berechnen
            total_pct = sum(c.get("coverage_pct", 0) for c in p.symptom_coverage) / len(p.symptom_coverage) if p.symptom_coverage else 0
            full = sum(1 for c in p.symptom_coverage if c.get("coverage_pct", 0) >= 85)
            partial = sum(1 for c in p.symptom_coverage if 60 <= c.get("coverage_pct", 0) < 85)
            insuff = sum(1 for c in p.symptom_coverage if c.get("coverage_pct", 0) < 60)

            st.metric(t("coverage_total"), f"~{total_pct:.0f}%")
            col_f, col_p, col_i = st.columns(3)
            col_f.metric(t("coverage_full"), f"{full}/{len(p.symptom_coverage)}")
            col_p.metric(t("coverage_partial"), f"{partial}/{len(p.symptom_coverage)}")
            col_i.metric(t("coverage_insufficient"), f"{insuff}/{len(p.symptom_coverage)}")

            # Formale Coverage-Metrik nach Paper-Definition:
            # C(S) = |{s in S : exists d in D, explains(d,s)}| / |S|
            # Ein Symptom gilt als "erklaert" wenn coverage_pct >= 60%
            explained = sum(1 for c in p.symptom_coverage if c.get("coverage_pct", 0) >= 60)
            formal_coverage = explained / len(p.symptom_coverage) if p.symptom_coverage else 0
            st.markdown("---")
            st.markdown(f"**{t('coverage_formal_title')}**")
            st.metric(t("coverage_formal_metric"),
                      f"{explained}/{len(p.symptom_coverage)} = {formal_coverage:.0%}")
            if formal_coverage < 1.0:
                st.warning(t("coverage_formal_warning"))

        # Legacy-Freitext
        p.coverage_analysis = st.text_area(
            t("ax1_coverage_label"),
            value=p.coverage_analysis,
            placeholder=t("ax1_coverage_placeholder")
        )

        st.markdown("---")

        # ── Ij: PRIORISIERTER UNTERSUCHUNGSPLAN ──
        st.subheader(t("ax1_plan_next_steps"))

        with st.form("inv_plan_form"):
            col1, col2 = st.columns(2)
            inv_name = col1.text_input(t("inv_plan_investigation"))
            inv_fach = col2.text_input(t("inv_plan_fachgebiet"))
            col3, col4 = st.columns(2)
            inv_prio = col3.selectbox(t("inv_plan_priority"), [
                t("inv_plan_dringend"), t("inv_plan_wichtig"), t("inv_plan_verlauf")
            ])
            inv_reason = col4.text_input(t("inv_plan_reason"))
            if st.form_submit_button(t("inv_plan_add")):
                p.investigation_plans.append(asdict(InvestigationPlan(
                    investigation=inv_name, fachgebiet=inv_fach,
                    priority=inv_prio, reason=inv_reason
                )))
                st.rerun()

        if p.investigation_plans and HAS_PANDAS:
            df_inv = pd.DataFrame(p.investigation_plans)[
                ["priority", "investigation", "fachgebiet", "reason"]]
            st.table(df_inv)

        # Legacy-Freitext
        p.investigation_plan = st.text_area(
            t("ax1_plan_next_steps"),
            value=p.investigation_plan,
            key="inv_plan_legacy"
        )

    # --- Therapieresistenz-Tracking (Sprint 2) ---
    with tab_therapy_resist:
        st.subheader(t("therapy_resist_subheader"))
        with st.form("therapy_resist_form"):
            tr_name = st.text_input(t("therapy_resist_treatment"), key="tr_name")
            col1, col2, col3 = st.columns(3)
            tr_type = col1.selectbox(t("therapy_resist_type"), [
                t("therapy_resist_type_medication"),
                t("therapy_resist_type_psychotherapy"),
                t("therapy_resist_type_other")
            ], key="tr_type")
            tr_start = col2.text_input(t("therapy_resist_start"), key="tr_start")
            tr_end = col3.text_input(t("therapy_resist_end"), key="tr_end")
            col4, col5 = st.columns(2)
            tr_response = col4.selectbox(t("therapy_resist_response"), [
                t("therapy_resist_response_none"),
                t("therapy_resist_response_partial"),
                t("therapy_resist_response_full")
            ], key="tr_response")
            tr_reason = col5.text_input(t("therapy_resist_reason"), key="tr_reason")
            tr_notes = st.text_area(t("therapy_resist_notes"), key="tr_notes")
            if st.form_submit_button(t("therapy_resist_add")):
                if tr_name.strip():
                    p.treatment_attempts.append(asdict(TreatmentAttempt(
                        treatment=tr_name.strip(),
                        treatment_type=tr_type,
                        start_date=tr_start,
                        end_date=tr_end,
                        response=tr_response,
                        reason_stopped=tr_reason,
                        notes=tr_notes
                    )))
                    st.rerun()

        if p.treatment_attempts and HAS_PANDAS:
            df_tr = pd.DataFrame(p.treatment_attempts)[
                ["treatment", "treatment_type", "start_date", "end_date",
                 "response", "reason_stopped", "notes"]]
            st.table(df_tr)
        elif p.treatment_attempts:
            for ta in p.treatment_attempts:
                st.write(f"- {ta.get('treatment','')} ({ta.get('treatment_type','')}) "
                         f"{ta.get('start_date','')} - {ta.get('end_date','')}: "
                         f"{ta.get('response','')}")


# ===================================================================
# ACHSE II: BIOGRAPHIE & PERSÖNLICHKEIT
# ===================================================================

elif menu == t("nav_axis2"):
    st.markdown(f"<div class='axis-header'>{t('header_axis2')}</div>",
                unsafe_allow_html=True)
    p = get_patient()

    tab_bio, tab_formative, tab_conflicts, tab_pid5 = st.tabs([
        t("ax2_tab_bio"), t("ax2_tab_formative"),
        t("ax2_tab_conflicts"), t("ax2_tab_pid5")
    ])

    with tab_bio:
        p.education = st.text_area(t("ax2_education"), value=p.education)
        p.iq_estimate = st.text_input(t("ax2_iq"), value=p.iq_estimate)
        p.developmental_history = st.text_area(
            t("ax2_developmental"),
            value=p.developmental_history
        )

    with tab_formative:
        st.subheader(t("ax2_tab_formative"))
        with st.form("formative_form"):
            fe_desc = st.text_area(t("ax2_formative_desc"), key="fe_desc")
            col1, col2 = st.columns(2)
            fe_age = col1.text_input(t("ax2_formative_age"), key="fe_age")
            fe_impact = col2.text_input(t("ax2_formative_impact"), key="fe_impact")
            if st.form_submit_button(t("ax2_formative_add")):
                if fe_desc.strip():
                    p.formative_experiences.append(asdict(FormativeExperience(
                        description=fe_desc.strip(),
                        age_period=fe_age,
                        impact=fe_impact,
                        date_added=str(datetime.date.today())
                    )))
                    st.rerun()

        if p.formative_experiences and HAS_PANDAS:
            df_fe = pd.DataFrame(p.formative_experiences)[
                ["description", "age_period", "impact", "date_added"]]
            st.table(df_fe)
        elif p.formative_experiences:
            for fe in p.formative_experiences:
                st.write(f"- {fe.get('description','')} ({fe.get('age_period','')})")

    with tab_conflicts:
        st.subheader(t("ax2_tab_conflicts"))
        with st.form("conflict_form"):
            cc_name = st.text_input(t("ax2_conflict_name"), key="cc_name")
            cc_desc = st.text_area(t("ax2_conflict_desc"), key="cc_desc")
            if st.form_submit_button(t("ax2_conflict_add")):
                if cc_name.strip():
                    p.core_conflicts.append(asdict(CoreConflict(
                        conflict=cc_name.strip(),
                        description=cc_desc,
                        date_added=str(datetime.date.today())
                    )))
                    st.rerun()

        if p.core_conflicts and HAS_PANDAS:
            df_cc = pd.DataFrame(p.core_conflicts)[
                ["conflict", "description", "date_added"]]
            st.table(df_cc)
        elif p.core_conflicts:
            for cc in p.core_conflicts:
                st.write(f"- **{cc.get('conflict','')}**: {cc.get('description','')}")

    with tab_pid5:
        st.subheader(t("ax2_pid5_subheader"))
        st.write(t("ax2_pid5_instruction"))

        pid5_domains = get_pid5_domains()
        domain_scores = {}
        for domain_key, domain in pid5_domains.items():
            st.markdown(f"**{domain['label']}** ({domain['icd11_trait']})")
            scores = []
            for i, item in enumerate(domain["items"]):
                val = st.slider(item, 0, 3, 0, key=f"pid5_{domain_key}_{i}")
                scores.append(val)
            domain_mean = sum(scores) / len(scores) if scores else 0
            domain_scores[domain_key] = round(domain_mean, 2)
            st.caption(f"{t('ax2_pid5_domain_mean')}: {domain_mean:.2f}")
            st.markdown("---")

        # PID-5 Profil speichern
        p.pid5_profile = PID5Profile(
            negative_affectivity=domain_scores.get("negative_affectivity", 0),
            detachment=domain_scores.get("detachment", 0),
            antagonism=domain_scores.get("antagonism", 0),
            disinhibition=domain_scores.get("disinhibition", 0),
            psychoticism=domain_scores.get("psychoticism", 0),
            anankastia=domain_scores.get("anankastia", 0)
        )

        # Radar-Chart
        if HAS_PLOTLY:
            st.subheader(t("ax2_pid5_radar_title"))
            categories = [d["label"] for d in pid5_domains.values()]
            values = list(domain_scores.values())
            values.append(values[0])  # Kreis schließen
            categories.append(categories[0])

            fig = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='PID-5',
                line_color='#268bd2'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 3])),
                showlegend=False,
                title=t("ax2_pid5_chart_title")
            )
            st.plotly_chart(fig, use_container_width=True)


# ===================================================================
# ACHSE III: MEDIZINISCHE SYNOPSE (IIIa - IIIm, SYMMETRISCH ZU ACHSE I)
# ===================================================================

elif menu == t("nav_axis3"):
    st.markdown(f"<div class='axis-header'>{t('header_axis3')}</div>",
                unsafe_allow_html=True)
    p = get_patient()

    # 13 Subachsen als Tabs (in 2 Reihen organisiert via Expander + Tabs)
    tab_acute, tab_chronic, tab_contrib, tab_rem, tab_remf = st.tabs([
        t("ax3_tab_acute"),
        t("ax3_tab_chronic"),
        t("ax3_tab_contributing"),
        t("ax3_tab_remitted"),
        t("ax3_tab_rem_factors"),
    ])

    # --- IIIa: Akute medizinische Diagnosen ---
    _lang = st.session_state.get("lang", "de")
    with tab_acute:
        st.subheader(t("ax3_acute_subheader"))
        with st.form("med_acute_form"):
            mc_name = st.text_input(t("ax3_med_diag_name"), key="iiia_name")
            col1, col2 = st.columns(2)
            if HAS_CODE_DB:
                _icd11_all = [""] + _load_code_options("icd11", _lang)
                _dsm5_all = [""] + _load_code_options("dsm5", _lang)
                mc_code_sel = col1.selectbox(t("ax3_med_diag_code"), _icd11_all, key="iiia_code")
                mc_dsm_sel = col2.selectbox(t("ax3_med_diag_dsm_code"), _dsm5_all, key="iiia_dsm")
                col_m1, col_m2 = st.columns(2)
                mc_code_man = col_m1.text_input(t("code_manual_icd11"), key="iiia_code_man")
                mc_dsm_man = col_m2.text_input(t("code_manual_dsm5"), key="iiia_dsm_man")
            else:
                mc_code_sel, mc_dsm_sel = "", ""
                mc_code_man = col1.text_input(t("ax3_med_diag_code"), key="iiia_code")
                mc_dsm_man = col2.text_input(t("ax3_med_diag_dsm_code"), key="iiia_dsm")
            mc_evidence = st.text_area(t("ax3_evidence"), key="iiia_evidence")
            if st.form_submit_button(t("ax3_add_condition")):
                mc_code = _extract_code(mc_code_sel) if mc_code_sel else mc_code_man.strip()
                mc_dsm = _extract_code(mc_dsm_sel) if mc_dsm_sel else mc_dsm_man.strip()
                if mc_dsm and not mc_code:
                    mc_code = get_cross_mapped_code("dsm5", mc_dsm, "icd11")
                elif mc_code and not mc_dsm:
                    mc_dsm = get_cross_mapped_code("icd11", mc_code, "dsm5")
                if not mc_name.strip() and mc_code:
                    mc_name = get_code_title("icd11", mc_code, _lang)
                if mc_name.strip() or mc_code:
                    p.med_diagnoses_acute.append(asdict(MedicalCondition(
                        name=mc_name, icd11_code=mc_code, dsm5_code=mc_dsm,
                        status="akut", evidence=mc_evidence
                    )))
                    st.rerun()
        for d in p.med_diagnoses_acute:
            st.error(f"🔴 {d['name']} ({d.get('icd11_code','')}/{d.get('dsm5_code','')})")

    # --- IIIb: Chronische medizinische Diagnosen (vollständig erklärend) ---
    with tab_chronic:
        st.subheader(t("ax3_chronic_subheader"))
        with st.form("med_chronic_form"):
            mc_name = st.text_input(t("ax3_med_diag_name"), key="iiib_name")
            col1, col2 = st.columns(2)
            if HAS_CODE_DB:
                mc_code_sel = col1.selectbox(t("ax3_med_diag_code"), _icd11_all, key="iiib_code")
                mc_dsm_sel = col2.selectbox(t("ax3_med_diag_dsm_code"), _dsm5_all, key="iiib_dsm")
                col_m1, col_m2 = st.columns(2)
                mc_code_man = col_m1.text_input(t("code_manual_icd11"), key="iiib_code_man")
                mc_dsm_man = col_m2.text_input(t("code_manual_dsm5"), key="iiib_dsm_man")
            else:
                mc_code_sel, mc_dsm_sel = "", ""
                mc_code_man = col1.text_input(t("ax3_med_diag_code"), key="iiib_code")
                mc_dsm_man = col2.text_input(t("ax3_med_diag_dsm_code"), key="iiib_dsm")
            mc_causality = st.selectbox(
                t("ax3_causality_label"),
                [t("ax3_causality_full"), t("ax3_causality_contributing"),
                 t("ax3_causality_independent")],
                key="iiib_causality"
            )
            mc_evidence = st.text_area(t("ax3_evidence"), key="iiib_evidence")
            if st.form_submit_button(t("ax3_add_condition")):
                mc_code = _extract_code(mc_code_sel) if mc_code_sel else mc_code_man.strip()
                mc_dsm = _extract_code(mc_dsm_sel) if mc_dsm_sel else mc_dsm_man.strip()
                if mc_dsm and not mc_code:
                    mc_code = get_cross_mapped_code("dsm5", mc_dsm, "icd11")
                elif mc_code and not mc_dsm:
                    mc_dsm = get_cross_mapped_code("icd11", mc_code, "dsm5")
                if not mc_name.strip() and mc_code:
                    mc_name = get_code_title("icd11", mc_code, _lang)
                if mc_name.strip() or mc_code:
                    p.med_diagnoses_chronic.append(asdict(MedicalCondition(
                        name=mc_name, icd11_code=mc_code, dsm5_code=mc_dsm,
                        status="chronisch", causality=mc_causality,
                        evidence=mc_evidence
                    )))
                    st.rerun()
        for d in p.med_diagnoses_chronic:
            st.warning(f"🟡 {d['name']} ({d.get('icd11_code','')}) [{d.get('causality','')}]")

    # --- IIIc: Beitragende medizinische Faktoren ---
    with tab_contrib:
        st.subheader(t("ax3_contributing_subheader"))
        with st.form("med_contrib_form"):
            mc_name = st.text_input(t("ax3_med_diag_name"), key="iiic_name")
            if HAS_CODE_DB:
                mc_code_sel = st.selectbox(t("ax3_med_diag_code"), _icd11_all, key="iiic_code")
                mc_code_man = st.text_input(t("code_manual_icd11"), key="iiic_code_man")
            else:
                mc_code_sel = ""
                mc_code_man = st.text_input(t("ax3_med_diag_code"), key="iiic_code")
            mc_evidence = st.text_area(t("ax3_evidence"), key="iiic_evidence")
            if st.form_submit_button(t("ax3_add_condition")):
                mc_code = _extract_code(mc_code_sel) if mc_code_sel else mc_code_man.strip()
                if not mc_name.strip() and mc_code:
                    mc_name = get_code_title("icd11", mc_code, _lang)
                if mc_name.strip() or mc_code:
                    p.med_diagnoses_contributing.append(asdict(MedicalCondition(
                        name=mc_name, icd11_code=mc_code,
                        status="aktiv", causality="beitragend",
                        evidence=mc_evidence
                    )))
                    st.rerun()
        for d in p.med_diagnoses_contributing:
            st.info(f"◐ {d['name']} ({d.get('icd11_code','')})")

    # --- IIId: Remittierte medizinische Erkrankungen ---
    with tab_rem:
        st.subheader(t("ax3_remitted_subheader"))
        with st.form("med_remitted_form"):
            mr_name = st.text_input(t("ax3_med_rem_name"), key="iiid_name")
            mr_factors = st.multiselect(t("ax3_med_rem_factors"),
                                        get_remission_factors(), key="iiid_factors")
            mr_evidence = st.text_area(t("ax3_med_rem_evidence"), key="iiid_evidence")
            if st.form_submit_button(t("ax3_med_rem_submit")):
                p.med_diagnoses_remitted.append(asdict(MedicalCondition(
                    name=mr_name, status="remittiert",
                    evidence=mr_evidence, remission_factors=mr_factors
                )))
                st.rerun()
        for d in p.med_diagnoses_remitted:
            factors = ", ".join(d.get("remission_factors", []))
            st.success(f"✅ {d['name']} ({factors})")

    # --- IIIe: Remissionsfaktoren ---
    with tab_remf:
        st.subheader(t("ax3_rem_factors_subheader"))
        st.info(t("ax3_rem_factors_info"))

    # --- Zweite Reihe Tabs: IIIf-IIIm ---
    tab_treat, tab_compl, tab_susp, tab_cov = st.tabs([
        t("ax3_tab_treatment"),
        t("ax3_tab_compliance"),
        t("ax3_tab_suspected"),
        t("ax3_tab_coverage"),
    ])

    # --- IIIf: Medizinische Behandlungsgeschichte ---
    with tab_treat:
        st.subheader(t("ax3_treatment_subheader"))
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**{t('ax3_med_treatment_current')}**")
            p.med_treatment_current = st.text_area(
                t("ax3_med_treatment_current"),
                value=p.med_treatment_current,
                key="iiif_current", label_visibility="collapsed"
            )
        with col2:
            st.write(f"**{t('ax3_med_treatment_past')}**")
            p.med_treatment_past = st.text_area(
                t("ax3_med_treatment_past"),
                value=p.med_treatment_past,
                key="iiif_past", label_visibility="collapsed"
            )

    # --- IIIg: Medizinische Therapietreue ---
    with tab_compl:
        st.subheader(t("ax3_med_compliance_subheader"))
        c1, c2 = st.columns(2)
        p.med_compliance_self = c1.slider(
            t("ax3_med_compliance_self"), 0, 10,
            p.med_compliance_self, key="iiig_self")
        p.med_compliance_ext = c2.slider(
            t("ax3_med_compliance_ext"), 0, 10,
            p.med_compliance_ext, key="iiig_ext")

    # --- IIIh: Verdachtsdiagnosen (medizinisch) ---
    with tab_susp:
        st.subheader(t("ax3_suspected_subheader"))
        with st.form("med_suspected_form"):
            ms_name = st.text_input(t("ax3_med_diag_name"), key="iiih_name")
            if HAS_CODE_DB:
                ms_code_sel = st.selectbox(t("ax3_med_diag_code"), _icd11_all, key="iiih_code")
                ms_code_man = st.text_input(t("code_manual_icd11"), key="iiih_code_man")
            else:
                ms_code_sel = ""
                ms_code_man = st.text_input(t("ax3_med_diag_code"), key="iiih_code")
            ms_evidence = st.text_area(t("ax3_evidence"), key="iiih_evidence")
            if st.form_submit_button(t("ax3_add_condition")):
                ms_code = _extract_code(ms_code_sel) if ms_code_sel else ms_code_man.strip()
                if not ms_name.strip() and ms_code:
                    ms_name = get_code_title("icd11", ms_code, _lang)
                if ms_name.strip() or ms_code:
                    p.med_diagnoses_suspected.append(asdict(MedicalCondition(
                        name=ms_name, icd11_code=ms_code,
                        status="Verdacht", evidence=ms_evidence
                    )))
                    st.rerun()
        for d in p.med_diagnoses_suspected:
            st.markdown(
                f"<div class='status-alert suspected'>? {t('ax3_med_suspected_prefix')}: "
                f"{esc(d['name'])} ({esc(d.get('icd11_code',''))})</div>",
                unsafe_allow_html=True
            )

    # --- IIIi: Medizinische Abdeckungsanalyse ---
    with tab_cov:
        st.subheader(t("ax3_coverage_subheader"))
        st.info(t("ax3_med_coverage_info"))
        p.med_coverage_analysis = st.text_area(
            t("ax3_med_coverage_label"),
            value=p.med_coverage_analysis,
            key="iiii_coverage"
        )

    # --- Dritte Reihe: IIIj-IIIm ---
    tab_plan, tab_caus, tab_gen, tab_med = st.tabs([
        t("ax3_tab_plan"),
        t("ax3_tab_causality"),
        t("ax3_tab_genetics"),
        t("ax3_tab_medication"),
    ])

    # --- IIIj: Medizinischer Untersuchungsplan ---
    with tab_plan:
        st.subheader(t("ax3_plan_subheader"))
        p.med_investigation_plan = st.text_area(
            t("ax3_med_plan_label"),
            value=p.med_investigation_plan,
            key="iiij_plan"
        )

    # --- IIIk: Kausalitätsanalyse ---
    with tab_caus:
        st.subheader(t("ax3_causality_subheader"))
        st.info(t("ax3_causality_iiib_info"))

        # Alle medizinischen Diagnosen sammeln (aus allen Subachsen)
        all_med = (p.med_diagnoses_acute + p.med_diagnoses_chronic +
                   p.med_diagnoses_contributing + p.medical_conditions)

        causality_full_text = t("ax3_causality_full")
        causality_contrib_text = t("ax3_causality_contributing")
        iiib = [c for c in all_med if causality_full_text in c.get("causality", "")]
        iiic = [c for c in all_med if causality_contrib_text in c.get("causality", "")]

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**{t('ax3_iiib_header')}**")
            for c in iiib:
                st.error(f"⬤ {c['name']} ({c.get('icd11_code', '')})")
            if not iiib:
                st.caption("—")
        with col2:
            st.write(f"**{t('ax3_iiic_header')}**")
            for c in iiic:
                st.warning(f"◐ {c['name']} ({c.get('icd11_code', '')})")
            if not iiic:
                st.caption("—")

    # --- IIIl: Genetik & Familiäre Belastung ---
    with tab_gen:
        st.subheader(t("ax3_genetics_subheader"))
        p.genetic_factors = st.text_area(t("ax3_genetic"),
                                         value=p.genetic_factors, key="iiil_genetic")
        p.family_history = st.text_area(t("ax3_family_history"),
                                         value=p.family_history, key="iiil_family")

    # --- IIIm: Medikamentenanamnese & Interaktionen ---
    with tab_med:
        st.subheader(t("ax3_medication_subheader"))
        with st.form("medication_form"):
            col1, col2, col3 = st.columns(3)
            med_name = col1.text_input(t("ax3_medication_name"), key="iiim_name")
            med_dose = col2.text_input(t("ax3_medication_dose"), key="iiim_dose")
            med_unit = col3.text_input(t("ax3_medication_unit"), key="iiim_unit")
            col4, col5 = st.columns(2)
            med_purpose = col4.text_input(t("ax3_medication_purpose"), key="iiim_purpose")
            med_since = col5.text_input(t("ax3_medication_since"), key="iiim_since")
            med_schedule = st.text_input(t("ax3_medication_schedule"), key="iiim_schedule")
            med_effect = st.text_input(t("ax3_medication_effect"), key="iiim_effect")
            med_rating = st.slider(t("ax3_medication_rating"), 0, 10, 5, key="iiim_rating")
            med_side = st.text_input(t("ax3_medication_side_effects"), key="iiim_side")
            med_inter = st.text_input(t("ax3_medication_interactions"), key="iiim_inter")
            if st.form_submit_button(t("ax3_medication_add")):
                p.medications.append(asdict(MedicationEntry(
                    name=med_name, dose=med_dose, unit=med_unit,
                    purpose=med_purpose, since=med_since,
                    schedule=med_schedule, effect=med_effect,
                    effect_rating=med_rating,
                    side_effects=med_side, interactions=med_inter
                )))
                st.rerun()

        if p.medications and HAS_PANDAS:
            df = pd.DataFrame(p.medications)[
                ["name", "dose", "unit", "purpose", "since", "schedule",
                 "effect", "effect_rating", "side_effects"]]
            st.table(df)


# ===================================================================
# ACHSE IV: UMWELT & FUNKTION
# ===================================================================

elif menu == t("nav_axis4"):
    st.markdown(f"<div class='axis-header'>{t('header_axis4')}</div>",
                unsafe_allow_html=True)
    st.info(t("ax4_see_gate6"))
    p = get_patient()

    st.subheader(t("ax4_stressors_subheader"))
    _stressor_options = get_stressors()
    _valid_defaults = [s for s in p.functioning.psychosocial_stressors if s in _stressor_options]
    stressors = st.multiselect(
        t("ax4_stressors_select"),
        _stressor_options,
        default=_valid_defaults
    )
    p.functioning.psychosocial_stressors = stressors

    st.markdown("---")

    # --- Bezugspersonen & Behandlungsnetzwerk ---
    st.subheader(t("ax4_contacts_subheader"))
    with st.form("contact_person_form"):
        col1, col2 = st.columns(2)
        cp_name = col1.text_input(t("ax4_contact_name"), key="cp_name")
        cp_role = col2.selectbox(t("ax4_contact_role"), [
            t("role_parent"), t("role_partner"), t("role_child"), t("role_sibling"),
            t("role_gp"), t("role_specialist"), t("role_therapist"),
            t("role_social_worker"), t("role_caregiver"), t("role_employer"), t("role_other")
        ], key="cp_role")
        col3, col4 = st.columns(2)
        cp_inst = col3.text_input(t("ax4_contact_institution"), key="cp_inst")
        cp_phone = col4.text_input(t("ax4_contact_phone"), key="cp_phone")
        cp_notes = st.text_input(t("ax4_contact_notes"), key="cp_notes")
        if st.form_submit_button(t("ax4_contact_add")):
            if cp_name.strip():
                p.contact_persons.append(asdict(ContactPerson(
                    name=cp_name.strip(), role=cp_role,
                    institution=cp_inst, phone=cp_phone, notes=cp_notes
                )))
                st.rerun()

    if p.contact_persons and HAS_PANDAS:
        df_cp = pd.DataFrame(p.contact_persons)[
            ["name", "role", "institution", "phone", "notes"]]
        st.table(df_cp)
    elif p.contact_persons:
        for cp in p.contact_persons:
            st.write(f"- **{cp.get('name','')}** ({cp.get('role','')}): {cp.get('institution','')}")

    st.markdown("---")

    # --- ICF-Codes (Funktionsfähigkeit & Behinderung) ---
    st.subheader(t("ax4_icf_subheader"))
    _lang = st.session_state.get("lang", "de")
    with st.form("icf_code_form"):
        if HAS_CODE_DB:
            _icf_opts = [""] + _load_code_options("icf", _lang)
            icf_sel = st.selectbox(t("ax4_icf_select"), _icf_opts, key="icf_sel")
            icf_manual = st.text_input(t("code_manual_icf"), key="icf_man")
        else:
            icf_sel = ""
            icf_manual = st.text_input(t("ax4_icf_select"), key="icf_code")
        icf_qualifier = st.selectbox(t("ax4_icf_qualifier"), [
            "0 - " + t("ax4_icf_q0"),
            "1 - " + t("ax4_icf_q1"),
            "2 - " + t("ax4_icf_q2"),
            "3 - " + t("ax4_icf_q3"),
            "4 - " + t("ax4_icf_q4"),
        ], key="icf_qual")
        icf_notes = st.text_input(t("ax4_icf_notes"), key="icf_notes")
        if st.form_submit_button(t("ax4_icf_add")):
            icf_code = _extract_code(icf_sel) if icf_sel else icf_manual.strip()
            if icf_code:
                icf_title = get_code_title("icf", icf_code, _lang) if HAS_CODE_DB else ""
                p.icf_codes.append({
                    "code": icf_code,
                    "title": icf_title or icf_code,
                    "qualifier": icf_qualifier.split(" - ")[0],
                    "qualifier_label": icf_qualifier,
                    "notes": icf_notes
                })
                st.rerun()

    if p.icf_codes and HAS_PANDAS:
        df_icf = pd.DataFrame(p.icf_codes)[["code", "title", "qualifier_label", "notes"]]
        df_icf.columns = ["Code", t("ax4_icf_title_col"), t("ax4_icf_qualifier"), t("ax4_icf_notes")]
        st.table(df_icf)
    elif p.icf_codes:
        for ic in p.icf_codes:
            st.write(f"- **{ic['code']}** {ic.get('title','')} [{ic.get('qualifier_label','')}]")

    st.markdown("---")

    st.subheader(t("ax4_functioning_summary"))
    col1, col2, col3 = st.columns(3)
    col1.metric("GAF", f"{p.functioning.gaf_score}/100")
    col2.metric("GdB", f"{p.functioning.gdb_score}")
    col3.metric(t("ax4_stressors_count"), f"{len(p.functioning.psychosocial_stressors)}")


# ===================================================================
# ACHSE V: INTEGRIERTES BEDINGUNGSMODELL
# ===================================================================

elif menu == t("nav_axis5"):
    st.markdown(f"<div class='axis-header'>{t('header_axis5')}</div>",
                unsafe_allow_html=True)
    p = get_patient()

    st.info(t("ax5_info"))

    tab_3p4p, tab_patho = st.tabs([
        t("ax5_tab_3p4p"),
        t("ax5_tab_patho")
    ])

    with tab_3p4p:
        # --- Bestehende Freitext-Felder (Rueckwaertskompatibilitaet) ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(t("ax5_predisposing"))
            predisposing = st.text_area(
                t("ax5_predisposing_placeholder"),
                value="\n".join(p.condition_model.predisposing),
                key="cm_predisposing"
            )
            p.condition_model.predisposing = [x for x in predisposing.split("\n") if x.strip()]

            st.subheader(t("ax5_precipitating"))
            precipitating = st.text_area(
                t("ax5_precipitating_placeholder"),
                value="\n".join(p.condition_model.precipitating),
                key="cm_precipitating"
            )
            p.condition_model.precipitating = [x for x in precipitating.split("\n") if x.strip()]

        with col2:
            st.subheader(t("ax5_perpetuating"))
            perpetuating = st.text_area(
                t("ax5_perpetuating_placeholder"),
                value="\n".join(p.condition_model.perpetuating),
                key="cm_perpetuating"
            )
            p.condition_model.perpetuating = [x for x in perpetuating.split("\n") if x.strip()]

            st.subheader(t("ax5_protective"))
            protective = st.text_area(
                t("ax5_protective_placeholder"),
                value="\n".join(p.condition_model.protective),
                key="cm_protective"
            )
            p.condition_model.protective = [x for x in protective.split("\n") if x.strip()]

        st.markdown("---")
        p.condition_model.narrative = st.text_area(
            t("ax5_narrative"),
            value=p.condition_model.narrative,
            height=200,
            placeholder=t("ax5_narrative_placeholder")
        )

        # --- Strukturierte Faktorenerfassung (Sprint 2) ---
        st.markdown("---")
        st.subheader(t("ax5_structured_subheader"))

        _axis_options = ["I", "II", "III", "IV"]
        _evidence_options = [
            t("ax5_evidence_confirmed"),
            t("ax5_evidence_probable"),
            t("ax5_evidence_hypothetical")
        ]

        _factor_configs = [
            ("predisposing", t("ax5_struct_for_predisposing"), "structured_predisposing"),
            ("precipitating", t("ax5_struct_for_precipitating"), "structured_precipitating"),
            ("perpetuating", t("ax5_struct_for_perpetuating"), "structured_perpetuating"),
            ("protective", t("ax5_struct_for_protective"), "structured_protective"),
        ]

        for factor_key, factor_label, attr_name in _factor_configs:
            st.markdown(f"**{factor_label}**")
            with st.form(f"struct_{factor_key}_form"):
                col_t, col_a, col_e = st.columns([3, 1, 1])
                sf_text = col_t.text_input(t("ax5_struct_text"), key=f"sf_{factor_key}_text")
                sf_axis = col_a.selectbox(t("ax5_struct_axis"), _axis_options,
                                          key=f"sf_{factor_key}_axis")
                sf_evidence = col_e.selectbox(t("ax5_struct_evidence"), _evidence_options,
                                              key=f"sf_{factor_key}_ev")
                if st.form_submit_button(t("ax5_struct_add")):
                    if sf_text.strip():
                        getattr(p, attr_name).append(asdict(StructuredFactor(
                            text=sf_text.strip(),
                            source_axis=sf_axis,
                            evidence_level=sf_evidence
                        )))
                        st.rerun()

            current_factors = getattr(p, attr_name)
            if current_factors and HAS_PANDAS:
                df_sf = pd.DataFrame(current_factors)
                st.table(df_sf)
            elif current_factors:
                for sf in current_factors:
                    st.write(f"- [{sf.get('source_axis','')}] {sf.get('text','')} "
                             f"({sf.get('evidence_level','')})")

    with tab_patho:
        st.subheader(t("ax5_patho_subheader"))
        st.info(t("ax5_patho_info"))

        p.pathophysiological_model.genetic_neurobiological = st.text_area(
            t("ax5_patho_genetic"),
            value=p.pathophysiological_model.genetic_neurobiological,
            placeholder=t("ax5_patho_genetic_placeholder"),
            key="patho_genetic"
        )
        p.pathophysiological_model.psychological_developmental = st.text_area(
            t("ax5_patho_psychological"),
            value=p.pathophysiological_model.psychological_developmental,
            placeholder=t("ax5_patho_psychological_placeholder"),
            key="patho_psych"
        )
        p.pathophysiological_model.environmental_situational = st.text_area(
            t("ax5_patho_environmental"),
            value=p.pathophysiological_model.environmental_situational,
            placeholder=t("ax5_patho_environmental_placeholder"),
            key="patho_env"
        )


# ===================================================================
# ACHSE VI: BELEGSAMMLUNG
# ===================================================================

elif menu == t("nav_axis6"):
    st.markdown(f"<div class='axis-header'>{t('header_axis6')}</div>",
                unsafe_allow_html=True)
    p = get_patient()

    with st.form("evidence_form"):
        col1, col2, col3 = st.columns([1, 2, 2])
        e_axis = col1.selectbox(t("ax6_axis_label"), ["I", "II", "III", "IV", "V"])
        e_type = col2.text_input(t("ax6_doc_type"))
        e_desc = col3.text_input(t("ax6_description"))
        e_assessment = st.text_area(t("ax6_assessment"), key="e_assessment")
        e_source = st.text_input(t("ax6_source"))
        if st.form_submit_button(t("ax6_submit")):
            p.evidence_entries.append(asdict(EvidenceEntry(
                axis=e_axis,
                document_type=e_type,
                description=e_desc,
                assessment=e_assessment,
                date=str(datetime.date.today()),
                source=e_source
            )))
            st.rerun()

    if p.evidence_entries and HAS_PANDAS:
        df = pd.DataFrame(p.evidence_entries)
        st.table(df)
    elif p.evidence_entries:
        for e in p.evidence_entries:
            st.write(f"{t('ax6_axis_label')} {e['axis']}: {e['document_type']} - {e['description']}")

    st.markdown("---")

    # --- CAVE Warnhinweise (Eingabe) ---
    st.subheader(f"CAVE / {t('cave_title')}")
    with st.form("cave_form"):
        cave_text = st.text_area(t("cave_text"), key="cave_text_input")
        col1, col2 = st.columns(2)
        cave_cat = col1.selectbox(t("cave_category"), [
            t("cave_cat_interaction"),
            t("cave_cat_lab_artifact"),
            t("cave_cat_contraindication"),
            t("cave_cat_temporal"),
            t("cave_cat_diagnostic"),
            t("cave_cat_other")
        ], key="cave_cat_input")
        cave_axis = col2.selectbox(t("cave_axis_ref"),
                                   ["I", "II", "III", "IV", "V", "VI"],
                                   key="cave_axis_input")
        if st.form_submit_button(t("cave_add")):
            if cave_text.strip():
                p.cave_alerts.append(asdict(CaveAlert(
                    text=cave_text.strip(),
                    category=cave_cat,
                    axis_ref=cave_axis,
                    date_added=str(datetime.date.today())
                )))
                st.rerun()

    if p.cave_alerts:
        for alert in p.cave_alerts:
            st.markdown(
                f"<div class='status-alert critical'>"
                f"<b>[{esc(alert.get('category',''))}]</b> {esc(alert.get('text',''))} "
                f"({t('cave_axis_ref')}: {esc(alert.get('axis_ref',''))})</div>",
                unsafe_allow_html=True
            )
    else:
        st.info(t("cave_empty"))

    st.markdown("---")

    # --- Symptomverlauf (Eingabe) ---
    st.subheader(t("symptom_timeline_title"))
    with st.form("timeline_form"):
        col1, col2 = st.columns(2)
        tl_symptom = col1.text_input(t("symptom_timeline_name"), key="tl_name")
        tl_onset = col2.text_input(t("symptom_timeline_onset"), key="tl_onset")
        col3, col4 = st.columns(2)
        tl_status = col3.text_input(t("symptom_timeline_status"), key="tl_status")
        tl_therapy = col4.text_input(t("symptom_timeline_therapy_response"), key="tl_therapy")
        if st.form_submit_button(t("symptom_timeline_add")):
            if tl_symptom.strip():
                p.symptom_timeline.append(asdict(SymptomTimeline(
                    symptom=tl_symptom.strip(),
                    onset=tl_onset,
                    current_status=tl_status,
                    therapy_response=tl_therapy
                )))
                st.rerun()

    if p.symptom_timeline and HAS_PANDAS:
        df_tl = pd.DataFrame(p.symptom_timeline)
        st.table(df_tl)
    elif p.symptom_timeline:
        for tl in p.symptom_timeline:
            st.write(f"{tl.get('symptom','')}: {tl.get('onset','')} \u2192 {tl.get('current_status','')}")

    st.markdown("---")

    # --- Kontakt- & Beobachtungsprotokoll ---
    st.subheader(t("ax6_contact_log_subheader"))
    with st.form("contact_log_form"):
        col1, col2 = st.columns(2)
        cl_date = col1.text_input(t("ax6_contact_log_date"),
                                   value=str(datetime.date.today()), key="cl_date")
        cl_type = col2.selectbox(t("ax6_contact_log_type"), [
            t("contact_type_phone"), t("contact_type_talk"), t("contact_type_observation"),
            t("contact_type_home_visit"), t("contact_type_collateral"),
            t("contact_type_email"), t("contact_type_other")
        ], key="cl_type")
        col3, col4 = st.columns(2)
        cl_person = col3.text_input(t("ax6_contact_log_person"), key="cl_person")
        cl_axis = col4.selectbox(t("ax6_contact_log_axis_ref"),
                                  ["I", "II", "III", "IV", "V", "VI", "\u2014"],
                                  key="cl_axis")
        cl_content = st.text_area(t("ax6_contact_log_content"), key="cl_content")
        if st.form_submit_button(t("ax6_contact_log_add")):
            if cl_content.strip():
                p.contact_log.append(asdict(ContactLog(
                    date=cl_date, contact_type=cl_type,
                    contact_person=cl_person, content=cl_content.strip(),
                    axis_ref=cl_axis if cl_axis != "\u2014" else ""
                )))
                st.rerun()

    if p.contact_log and HAS_PANDAS:
        df_cl = pd.DataFrame(p.contact_log)[
            ["date", "contact_type", "contact_person", "content", "axis_ref"]]
        st.table(df_cl)
    elif p.contact_log:
        for cl in p.contact_log:
            st.write(f"- [{cl.get('date','')}] {cl.get('contact_type','')}: "
                     f"{cl.get('content','')}")


# ===================================================================
# GESAMTSYNOPSE & EXPORT
# ===================================================================

elif menu == t("nav_synopsis"):
    st.markdown(f"<h1 style='text-align: center;'>{t('header_synopsis')}</h1>",
                unsafe_allow_html=True)
    p = get_patient()

    # --- Achse I ---
    st.markdown(f"<div class='axis-header'>{t('syn_axis1_header')}</div>",
                unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{t('syn_acute_chronic')}**")
        for d in p.diagnoses_acute:
            st.error(f"🔴 {d['name']} ({d.get('code_icd11','')}/{d.get('code_dsm5','')})")
        for d in p.diagnoses_chronic:
            st.warning(f"🟡 {d['name']} ({d.get('code_icd11','')}/{d.get('code_dsm5','')})")
        st.write(f"**{t('syn_remitted')}**")
        for d in p.diagnoses_remitted:
            factors = ", ".join(d.get("remission_factors", []))
            st.success(f"✅ {d['name']} ({t('ax1_rem_factors_label')}: {factors})")
    with col2:
        st.write(f"**{t('syn_diagnostic_certainty')}**")
        for d in p.diagnoses_suspected:
            st.markdown(f"<div class='status-alert suspected'>? {t('ax1_suspected_prefix')}: {esc(d['name'])}</div>",
                        unsafe_allow_html=True)
        for d in p.diagnoses_excluded:
            st.markdown(f"<div class='status-alert excluded'>✖ {t('ax1_excluded_prefix')}: {esc(d['name'])}</div>",
                        unsafe_allow_html=True)

    # --- Achse II ---
    st.markdown(f"<div class='axis-header'>{t('syn_axis2_header')}</div>",
                unsafe_allow_html=True)
    if HAS_PLOTLY:
        pid5 = p.pid5_profile
        categories = [t("syn_pid5_short_neg"), t("syn_pid5_short_det"),
                      t("syn_pid5_short_ant"), t("syn_pid5_short_dis"),
                      t("syn_pid5_short_psy"), t("syn_pid5_short_ana")]
        values = [pid5.negative_affectivity, pid5.detachment,
                  pid5.antagonism, pid5.disinhibition,
                  pid5.psychoticism, pid5.anankastia]
        values_closed = values + [values[0]]
        categories_closed = categories + [categories[0]]

        fig = go.Figure(data=go.Scatterpolar(
            r=values_closed, theta=categories_closed,
            fill='toself', line_color='#268bd2'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 3])),
            showlegend=False, height=350,
            title=t("syn_pid5_profile_title")
        )
        st.plotly_chart(fig, use_container_width=True)

    # Prägende Erfahrungen & Grundkonflikte in Synopsis
    if p.formative_experiences:
        st.write(f"**{t('ax2_tab_formative')}**")
        for fe in p.formative_experiences:
            st.write(f"- {fe.get('description','')} ({fe.get('age_period','')}) "
                     f"\u2192 {fe.get('impact','')}")
    if p.core_conflicts:
        st.write(f"**{t('ax2_tab_conflicts')}**")
        for cc in p.core_conflicts:
            st.write(f"- **{cc.get('conflict','')}**: {cc.get('description','')}")

    # --- HiTOP-Spektren ---
    if p.crosscutting_level1:
        st.markdown(f"<div class='axis-header'>{t('hitop_title')}</div>",
                    unsafe_allow_html=True)
        render_hitop_radar(p.hitop_profile)

    # --- Achse III ---
    st.markdown(f"<div class='axis-header'>{t('syn_axis3_header')}</div>",
                unsafe_allow_html=True)
    # Alle medizinischen Diagnosen zusammenführen
    all_med_syn = (p.med_diagnoses_acute + p.med_diagnoses_chronic +
                   p.med_diagnoses_contributing + p.medical_conditions)
    if all_med_syn and HAS_PANDAS:
        df = pd.DataFrame(all_med_syn)
        cols = [c for c in ["name", "icd11_code", "causality", "status"] if c in df.columns]
        st.table(df[cols])

    col1, col2 = st.columns(2)
    with col1:
        if p.med_diagnoses_suspected:
            st.write(f"**{t('ax3_suspected_subheader')}**")
            for d in p.med_diagnoses_suspected:
                st.markdown(
                    f"<div class='status-alert suspected'>? {esc(d['name'])}</div>",
                    unsafe_allow_html=True)
    with col2:
        if p.medications:
            st.write(f"**{t('ax3_medication_subheader')}**")
            for m in p.medications:
                st.caption(f"💊 {m.get('name','')} {m.get('dose','')}")

    # --- Achse IV ---
    st.markdown(f"<div class='axis-header'>{t('syn_axis4_header')}</div>",
                unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("GAF-Score", f"{p.functioning.gaf_score}/100")
    col2.metric("GdB", f"{p.functioning.gdb_score}")
    col3.metric(t("syn_stressors_prefix"), f"{len(p.functioning.psychosocial_stressors)}")
    if p.functioning.psychosocial_stressors:
        st.write(f"{t('syn_stressors_prefix')}: " + ", ".join(p.functioning.psychosocial_stressors))
    if p.contact_persons:
        st.write(f"**{t('ax4_contacts_subheader')}**")
        if HAS_PANDAS:
            df_cp = pd.DataFrame(p.contact_persons)
            _cp_cols = [c for c in ["name", "role", "institution", "phone"] if c in df_cp.columns]
            st.table(df_cp[_cp_cols] if _cp_cols else df_cp)
        else:
            for cp in p.contact_persons:
                st.write(f"- {cp.get('name','')} ({cp.get('role','')})")
    if p.icf_codes:
        st.write(f"**{t('ax4_icf_subheader')}**")
        if HAS_PANDAS:
            df_icf = pd.DataFrame(p.icf_codes)
            _icf_cols = [c for c in ["code", "title", "qualifier_label"] if c in df_icf.columns]
            st.table(df_icf[_icf_cols] if _icf_cols else df_icf)
        else:
            for ic in p.icf_codes:
                st.write(f"- {ic['code']} {ic.get('title','')} [{ic.get('qualifier_label','')}]")

    # --- Therapieresistenz-Tracking (Synopsis) ---
    if p.treatment_attempts:
        st.markdown(f"<div class='axis-header'>{t('syn_therapy_resist_header')}</div>",
                    unsafe_allow_html=True)
        if HAS_PANDAS:
            df_tr = pd.DataFrame(p.treatment_attempts)
            _tr_cols = [c for c in ["treatment", "treatment_type", "start_date", "end_date",
                         "response", "reason_stopped"] if c in df_tr.columns]
            st.table(df_tr[_tr_cols] if _tr_cols else df_tr)
        else:
            for ta in p.treatment_attempts:
                st.write(f"- {ta.get('treatment','')} ({ta.get('treatment_type','')}) "
                         f"{ta.get('start_date','')} - {ta.get('end_date','')}: "
                         f"{ta.get('response','')}")

    # --- CGI-Verlauf (Synopsis) ---
    if p.cgi_assessments:
        st.markdown(f"<div class='axis-header'>{t('syn_cgi_header')}</div>",
                    unsafe_allow_html=True)
        if HAS_PANDAS:
            df_cgi = pd.DataFrame(p.cgi_assessments)
            _cgi_cols = [c for c in ["date", "cgi_s", "cgi_i", "therapeutic_effect",
                          "side_effects", "notes"] if c in df_cgi.columns]
            st.table(df_cgi[_cgi_cols] if _cgi_cols else df_cgi)
        else:
            for ca in p.cgi_assessments:
                st.write(f"- [{ca.get('date','')}] CGI-S: {ca.get('cgi_s',0)}, "
                         f"CGI-I: {ca.get('cgi_i',0)}")

    # --- CGI-Assessment Eingabe (Synopsis) ---
    st.markdown(f"<div class='axis-header'>{t('cgi_subheader')}</div>",
                unsafe_allow_html=True)
    with st.form("cgi_form"):
        cgi_date = st.text_input(t("cgi_date"),
                                  value=str(datetime.date.today()), key="cgi_date")
        col1, col2 = st.columns(2)
        cgi_s_options = [t(f"cgi_s_{i}") for i in range(1, 8)]
        cgi_i_options = [t(f"cgi_i_{i}") for i in range(1, 8)]
        cgi_s = col1.selectbox(t("cgi_s_label"), cgi_s_options, key="cgi_s_sel")
        cgi_i = col2.selectbox(t("cgi_i_label"), cgi_i_options, key="cgi_i_sel")
        col3, col4 = st.columns(2)
        cgi_eff_options = [t(f"cgi_effect_{i}") for i in range(1, 5)]
        cgi_side_options = [t(f"cgi_side_{i}") for i in range(1, 5)]
        cgi_eff = col3.selectbox(t("cgi_effect_label"), cgi_eff_options, key="cgi_eff_sel")
        cgi_side = col4.selectbox(t("cgi_side_effects_label"), cgi_side_options, key="cgi_side_sel")
        cgi_notes = st.text_input(t("cgi_notes"), key="cgi_notes_input")
        if st.form_submit_button(t("cgi_add")):
            # Numerischen Wert aus der Option extrahieren
            cgi_s_val = cgi_s_options.index(cgi_s) + 1
            cgi_i_val = cgi_i_options.index(cgi_i) + 1
            cgi_eff_val = cgi_eff_options.index(cgi_eff) + 1
            cgi_side_val = cgi_side_options.index(cgi_side) + 1
            p.cgi_assessments.append(asdict(CGIAssessment(
                date=cgi_date,
                cgi_s=cgi_s_val,
                cgi_i=cgi_i_val,
                therapeutic_effect=cgi_eff_val,
                side_effects=cgi_side_val,
                notes=cgi_notes
            )))
            st.rerun()

    # --- Achse V ---
    st.markdown(f"<div class='axis-header'>{t('syn_axis5_header')}</div>",
                unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{t('syn_predisposing')}**", ", ".join(p.condition_model.predisposing) or "\u2014")
        st.write(f"**{t('syn_precipitating')}**", ", ".join(p.condition_model.precipitating) or "\u2014")
    with col2:
        st.write(f"**{t('syn_perpetuating')}**", ", ".join(p.condition_model.perpetuating) or "\u2014")
        st.write(f"**{t('syn_protective')}**", ", ".join(p.condition_model.protective) or "\u2014")
    if p.condition_model.narrative:
        st.info(f"**{t('syn_narrative_label')}**\n\n{p.condition_model.narrative}")

    # Strukturierte Faktoren in Synopsis
    _structured_lists = [
        ("syn_predisposing", p.structured_predisposing),
        ("syn_precipitating", p.structured_precipitating),
        ("syn_perpetuating", p.structured_perpetuating),
        ("syn_protective", p.structured_protective),
    ]
    has_structured = any(sl for _, sl in _structured_lists)
    if has_structured:
        st.markdown(f"**{t('syn_structured_factors')}**")
        for label_key, factor_list in _structured_lists:
            if factor_list:
                st.write(f"*{t(label_key)}*")
                for sf in factor_list:
                    st.write(f"- [{sf.get('source_axis','')}] {sf.get('text','')} "
                             f"({sf.get('evidence_level','')})")

    # Pathophysiologisches Kausalmodell in Synopsis
    pm = p.pathophysiological_model
    if pm.genetic_neurobiological or pm.psychological_developmental or pm.environmental_situational:
        st.markdown(f"<div class='axis-header'>{t('syn_patho_header')}</div>",
                    unsafe_allow_html=True)
        if pm.genetic_neurobiological:
            st.write(f"**{t('ax5_patho_genetic')}:** {pm.genetic_neurobiological}")
        if pm.psychological_developmental:
            st.write(f"**{t('ax5_patho_psychological')}:** {pm.psychological_developmental}")
        if pm.environmental_situational:
            st.write(f"**{t('ax5_patho_environmental')}:** {pm.environmental_situational}")

    # --- Achse VI ---
    st.markdown(f"<div class='axis-header'>{t('syn_axis6_header')}</div>",
                unsafe_allow_html=True)
    if p.evidence_entries and HAS_PANDAS:
        st.table(pd.DataFrame(p.evidence_entries))
    if p.contact_log:
        st.write(f"**{t('ax6_contact_log_subheader')}**")
        if HAS_PANDAS:
            df_cl = pd.DataFrame(p.contact_log)
            _cl_cols = [c for c in ["date", "contact_type", "contact_person",
                         "content", "axis_ref"] if c in df_cl.columns]
            st.table(df_cl[_cl_cols] if _cl_cols else df_cl)
        else:
            for cl in p.contact_log:
                st.write(f"- [{cl.get('date','')}] {cl.get('contact_type','')}: "
                         f"{cl.get('content','')}")

    # --- Abdeckungsanalyse ---
    # --- Strukturierte Abdeckungsanalyse ---
    st.markdown(f"<div class='axis-header'>{t('syn_coverage_header')}</div>",
                unsafe_allow_html=True)
    if p.symptom_coverage:
        if HAS_PANDAS:
            df_cov = pd.DataFrame(p.symptom_coverage)
            st.table(df_cov)
        total_pct = sum(c.get("coverage_pct", 0) for c in p.symptom_coverage) / len(p.symptom_coverage)
        st.metric(t("coverage_total"), f"~{total_pct:.0f}%")
    if p.coverage_analysis:
        st.markdown(
            f"<div class='coverage-gap'><b>{t('syn_unexplained')}</b><br/>"
            f"{esc(p.coverage_analysis)}</div>",
            unsafe_allow_html=True
        )
    elif not p.symptom_coverage:
        st.success(t("syn_no_unexplained"))

    # --- CAVE Warnhinweise ---
    if p.cave_alerts:
        st.markdown("<div class='axis-header' style='background-color:#dc322f;color:#fdf6e3;'>"
                    f"CAVE / {t('cave_title')}</div>",
                    unsafe_allow_html=True)
        for alert in p.cave_alerts:
            st.markdown(
                f"<div class='status-alert critical'>"
                f"<b>[{esc(alert.get('category',''))}]</b> {esc(alert.get('text',''))} "
                f"({t('cave_axis_ref')}: {esc(alert.get('axis_ref',''))})</div>",
                unsafe_allow_html=True
            )

    # --- Symptomverlauf ---
    if p.symptom_timeline:
        st.markdown(f"<div class='axis-header'>{t('symptom_timeline_title')}</div>",
                    unsafe_allow_html=True)
        if HAS_PANDAS:
            df_tl = pd.DataFrame(p.symptom_timeline)
            st.table(df_tl)

    # --- Export ---
    st.markdown("---")
    st.subheader(t("syn_export"))
    if st.button(t("syn_export_button")):
        export_data = {
            "export_date": str(datetime.datetime.now()),
            "system_version": t("syn_system_version"),
            "language": st.session_state.lang,
            "axes": {
                "I_psychische_profile": {
                    "acute": p.diagnoses_acute,
                    "chronic": p.diagnoses_chronic,
                    "remitted": p.diagnoses_remitted,
                    "suspected": p.diagnoses_suspected,
                    "excluded": p.diagnoses_excluded,
                    "compliance": {
                        "med_self": p.compliance_med_self,
                        "med_ext": p.compliance_med_ext,
                        "therapy": p.compliance_therapy
                    },
                    "investigation_plan": p.investigation_plan,
                    "coverage_analysis": p.coverage_analysis
                },
                "II_biographie": {
                    "education": p.education,
                    "iq": p.iq_estimate,
                    "developmental_history": p.developmental_history,
                    "formative_experiences": p.formative_experiences,
                    "core_conflicts": p.core_conflicts,
                    "pid5_profile": asdict(p.pid5_profile)
                },
                "III_medizinisch": {
                    "IIIa_acute": p.med_diagnoses_acute,
                    "IIIb_chronic": p.med_diagnoses_chronic,
                    "IIIc_contributing": p.med_diagnoses_contributing,
                    "IIId_remitted": p.med_diagnoses_remitted,
                    "IIIf_treatment_current": p.med_treatment_current,
                    "IIIf_treatment_past": p.med_treatment_past,
                    "IIIg_compliance": {
                        "self": p.med_compliance_self,
                        "external": p.med_compliance_ext
                    },
                    "IIIh_suspected": p.med_diagnoses_suspected,
                    "IIIi_coverage": p.med_coverage_analysis,
                    "IIIj_plan": p.med_investigation_plan,
                    "IIIk_conditions_legacy": p.medical_conditions,
                    "IIIl_genetic_factors": p.genetic_factors,
                    "IIIl_family_history": p.family_history,
                    "IIIm_medications": p.medications
                },
                "IV_umwelt_funktion": {
                    "gaf": p.functioning.gaf_score,
                    "gdb": p.functioning.gdb_score,
                    "stressors": p.functioning.psychosocial_stressors,
                    "contact_persons": p.contact_persons,
                    "icf_codes": p.icf_codes
                },
                "V_bedingungsmodell": {
                    **asdict(p.condition_model),
                    "structured_predisposing": p.structured_predisposing,
                    "structured_precipitating": p.structured_precipitating,
                    "structured_perpetuating": p.structured_perpetuating,
                    "structured_protective": p.structured_protective,
                    "pathophysiological_model": asdict(p.pathophysiological_model)
                },
                "VI_belegsammlung": {
                    "evidence_entries": p.evidence_entries,
                    "contact_log": p.contact_log
                }
            },
            "screening": {
                "crosscutting_level1": p.crosscutting_level1,
                "triggered_domains": p.crosscutting_triggered,
                "hitop_profile": asdict(p.hitop_profile)
            },
            "gatekeeper": p.gate_results,
            "cave_alerts": p.cave_alerts,
            "symptom_coverage": p.symptom_coverage,
            "investigation_plans": p.investigation_plans,
            "symptom_timeline": p.symptom_timeline,
            "treatment_attempts": p.treatment_attempts,
            "cgi_assessments": p.cgi_assessments
        }
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False,
                              default=str)
        st.download_button(
            label=t("syn_download"),
            data=json_str,
            file_name=f"diagnostic_export_{datetime.date.today()}.json",
            mime="application/json"
        )
        st.json(export_data)


# ===================================================================
# SESSION SAVE / LOAD (Sprint 2)
# ===================================================================

_SESSION_DIR = os.path.dirname(os.path.abspath(__file__))


def _save_session(filename: str):
    """Save current PatientData to JSON file."""
    p = get_patient()
    save_data = {
        "session_version": "v10",
        "saved_at": str(datetime.datetime.now()),
        "current_gate": st.session_state.current_gate,
        "lang": st.session_state.lang,
        "patient": asdict(p)
    }
    filepath = os.path.join(_SESSION_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False, default=str)
    return filepath


def _auto_save():
    """Auto-save session to default file (called on significant state changes)."""
    try:
        _save_session("diagnostic_session.json")
    except Exception:
        pass  # Auto-save failure is non-critical


def _load_session(filepath: str) -> bool:
    """Load PatientData from JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        pd_dict = data.get("patient", {})
        # Reconstruct nested dataclasses
        if "pid5_profile" in pd_dict:
            pd_dict["pid5_profile"] = PID5Profile(**pd_dict["pid5_profile"])
        if "hitop_profile" in pd_dict:
            pd_dict["hitop_profile"] = HiTOPProfile(**pd_dict["hitop_profile"])
        if "functioning" in pd_dict:
            pd_dict["functioning"] = FunctioningAssessment(**pd_dict["functioning"])
        if "condition_model" in pd_dict:
            pd_dict["condition_model"] = ConditionModel(**pd_dict["condition_model"])
        if "pathophysiological_model" in pd_dict:
            pd_dict["pathophysiological_model"] = PathophysiologicalModel(
                **pd_dict["pathophysiological_model"])
        # Create PatientData with safe defaults for missing fields
        valid_fields = {f.name for f in PatientData.__dataclass_fields__.values()}
        filtered = {k: v for k, v in pd_dict.items() if k in valid_fields}
        st.session_state.patient = PatientData(**filtered)
        st.session_state.current_gate = data.get("current_gate", 0)
        st.session_state.lang = data.get("lang", "de")
        return True
    except Exception as e:
        st.sidebar.warning(f"Session load error: {e}")
        return False


# --- Sidebar: Session Save/Load ---
st.sidebar.markdown("---")
st.sidebar.subheader(t("session_save"))

_session_filename = st.sidebar.text_input(
    t("session_filename_label"),
    value="diagnostic_session.json",
    key="session_filename"
)

col_save, col_load = st.sidebar.columns(2)
if col_save.button(t("session_save"), key="btn_save"):
    _save_session(_session_filename)
    st.sidebar.success(t("session_save_success"))

if col_load.button(t("session_load"), key="btn_load"):
    _load_path = os.path.join(_SESSION_DIR, _session_filename)
    if os.path.exists(_load_path):
        if _load_session(_load_path):
            st.sidebar.success(t("session_load_success"))
            st.rerun()
        else:
            st.sidebar.error(t("session_load_error"))
    else:
        st.sidebar.error(t("session_load_error"))

# Auto-load moved to top of file (before page render) for immediate display


# ===================================================================
# FOOTER
# ===================================================================

st.sidebar.markdown("---")
st.sidebar.warning(t("disclaimer_professional_use"))
st.sidebar.caption(
    f"{t('footer_line1')}\n\n"
    f"{t('footer_line2')}\n\n"
    f"{t('footer_line3')}\n\n"
    f"{t('footer_date_prefix')}: {datetime.date.today()}"
)

# Auto-save on every interaction (V10 feature)
_auto_save()
