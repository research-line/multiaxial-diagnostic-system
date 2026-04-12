# Multiaxial Diagnostic Expert System (V10)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18736725.svg)](https://doi.org/10.5281/zenodo.18736725)

A computer-assisted 6-axis research prototype for structured documentation and coding of psychiatric diagnostic reasoning. It integrates DSM-5-TR, ICD-11, and ICF within a single expert-system-style interface.

> ⚠️ **Kein Medizinprodukt / Not a Medical Device**
>
> Das multiaxial-diagnostic-system ist **kein Medizinprodukt** im Sinne der MDR
> (EU) 2017/745, **nicht klinisch validiert**, **nicht durch BfArM oder eine
> Benannte Stelle geprüft**, **nicht zertifiziert**. Es ist ein Softwareentwurf
> zur Erforschung von strukturierter Dokumentation und Kodierung diagnostischer
> Prozesse (6-Achsen-Modell, DSM-5-TR / ICD-11 / ICF-Integration) zu
> **Lehr-, Forschungs- und Softwareentwicklungszwecken**.
>
> - **Keine Diagnose.** Ausgaben sind strukturierte Kodierungsvorschläge, keine klinischen Diagnosen.
> - **Keine Therapieempfehlung.**
> - **Keine klinische Entscheidungsunterstützung** im Sinne der MDR-Zweckbestimmung.
>
> Diagnose und Behandlungsentscheidung bleiben qualifizierten Fachleuten
> vorbehalten (Ärztinnen/Ärzte, Psychotherapeutinnen/Psychotherapeuten).
>
> Unentgeltliche Open-Source-Schenkung. Haftung auf Vorsatz und grobe
> Fahrlässigkeit beschränkt (§ 521 BGB). Nutzung auf eigenes Risiko.
>
> *The multiaxial-diagnostic-system is **not a medical device** within the
> meaning of the EU MDR 2017/745, **not clinically validated**, **not reviewed
> or certified** by BfArM or any Notified Body. It is a software prototype
> for teaching, research, and software-engineering purposes exploring the
> structured documentation and coding of diagnostic reasoning. Outputs are
> structured coding proposals, not diagnoses, therapy recommendations, or
> clinical decision support in the regulatory sense. Diagnosis and treatment
> decisions remain reserved for qualified professionals.*

> **For qualified mental health professionals only.** This tool supports but does not replace clinical judgment. See the full legal notice in [`NOTICE`](NOTICE) and section *Legal Notice* below.

<img src="_data/screenshot.jpg" alt="Multiaxial Diagnostic System - Gatekeeper Interface" width="700">

## Overview

This system addresses the structural gap left by the abolition of the multiaxial system in DSM-5 (2013). It provides a comprehensive, multi-professional diagnostic framework with innovations that go beyond any previous classification system.

### The 6-Axis Model

| Axis | Name | Sub-axes | Primary Profession |
|------|------|----------|-------------------|
| I | Mental Health Profiles | Ia-Ij (10 sub-axes) | Psychologist / Psychiatrist |
| II | Biography & Development | Personality (PID-5), Education, IQ | Psychologist |
| III | Medical Synopsis | IIIa-IIIm (13 sub-axes, symmetric to Axis I) | Physician |
| IV | Environment & Functioning | ICF, WHODAS 2.0, GAF, GdB, CFI | Social Worker |
| V | Integrated Condition Model | 3P/4P Case Formulation | Interdisciplinary Team |
| VI | Evidence Collection & Data-Integrity Layer | Evidence Matrix, CAVE pattern notifications, Symptom Timeline | All Professions |

### Key Innovations

- **Formal Coverage Analysis** (Ii/IIIi): Set-based metric C(S) = |explained| / |total symptoms| plus percentage-based symptom-diagnosis matrix identifying unexplained symptoms
- **Symmetric Axis I/III Architecture**: Identical structural tools for psychologists and physicians
- **PRO/CONTRA Evidence Evaluation**: Structured evidence for/against each diagnosis with confidence estimation
- **CAVE pattern-based notifications**: Cross-axis rule-based notifications (drug-interaction patterns, lab artifacts, contraindication patterns) — *no automated clinical risk assessment*
- **Prioritized Investigation Plan**: 3-tier system (Urgent / Important / Monitoring)
- **Longitudinal Symptom Timeline**: Tracking onset, status, and therapy response over time
- **HiTOP Spectra**: Automatically computed from Cross-Cutting screening results
- **6-Step Gatekeeper Logic**: Implementing First's (2024) gold-standard differential diagnosis sequence
- **11 Disorder Modules**: Complete screening-to-diagnosis coverage via hierarchical state machine

## Scientific Paper

The theoretical foundation and clinical rationale for this system are described in the accompanying preprint:

> **Geiger, L.** (2026). *An Integrated Multiaxial Model for Computer-Assisted Psychiatric Diagnosis: Synthesis of DSM-5-TR, ICD-11, and ICF in a 6-Axis Expert System.* Zenodo. [https://doi.org/10.5281/zenodo.18736725](https://doi.org/10.5281/zenodo.18736725)

The preprint is available in English, German, and a combined bilingual edition:
- [`paper/Review_Multiaxiale_Diagnostik_v2_en.pdf`](paper/Review_Multiaxiale_Diagnostik_v2_en.pdf) -- English
- [`paper/Review_Multiaxiale_Diagnostik_v2_ger.pdf`](paper/Review_Multiaxiale_Diagnostik_v2_ger.pdf) -- German

### Data-Integrity & Input-Validation Layer (V10)

- **XSS Protection**: All user-supplied data HTML-escaped before rendering
- **GAF Deprecation Notice**: DSM-5 replaced GAF with WHODAS 2.0; system shows deprecation warning
- **Professional-Use Disclaimer**: Sidebar warning for qualified personnel only
- **Robust Input Parsing**: Likert scale extraction with fallback handling
- **Full Bilingual Coverage**: All UI strings (584 keys DE/EN) via `translations.json`, no hardcoded strings

## Diagnostic Testcenter (NEW)

A standalone web application for digital administration of all 16 validated screening instruments referenced in the paper. Supports both **remote client assessment** (link sharing) and **pen & paper** (print-friendly PDFs).

### Features

- **16 validated instruments** (PHQ-9, GAD-7, PCL-5, ITQ, AUDIT, C-SSRS, PQ-16, ASRS, AQ-10, OCI-R, SSS-8, DES-II, SCOFF, ISI, PID-5-BF, WHODAS 2.0) -- all freely available, bilingual (DE/EN)
- **Automatic scoring** with severity classification, color-coded thresholds, and clinical action guides
- **Test batteries**: Send multiple tests as a package -- client receives one link and works through all tests sequentially with progress tracking
- **Link sharing**: Clinician creates session → generates token URL → sends to client → client fills out remotely → clinician views results
- **Print-friendly output**: Single tests or bundles as printable HTML (pen & paper), with patient header, scoring tables, and references
- **Critical item alerts**: Suicidality screening (PHQ-9 Item 9, C-SSRS) triggers immediate warnings with emergency resources
- **REST API**: Full JSON API for programmatic integration (`/api/tests`, `/api/results/<token>`, `/api/score`)
- **Integration with main system**: Cross-Cutting screening in the Streamlit app (Gate 5) links directly to the Testcenter for recommended Level-2 instruments

### Testcenter Quick Start

```bash
cd _data/testcenter
pip install flask
python app.py
# → http://localhost:5050
```

### Included Instruments

| Instrument | Items | Domain | Axis | Scoring |
|-----------|-------|--------|------|---------|
| PHQ-9 | 9 | Depression | I | Sum (0-27), cutoff ≥10 |
| GAD-7 | 7 | Anxiety | I | Sum (0-21), cutoff ≥10 |
| PCL-5 | 20 | PTSD (DSM-5) | I | Sum + DSM-5 clusters |
| ITQ | 16 | PTSD/CPTSD (ICD-11) | I | Diagnostic algorithm |
| PQ-16 | 16 | Psychosis risk | I | Endorsement + distress |
| ASRS v1.1 | 6 | ADHD | I | Threshold count |
| AQ-10 | 10 | Autism spectrum | I | Directional sum |
| AUDIT | 10 | Alcohol use | I | Sum (0-40), 3 subscales |
| C-SSRS | 6 | Suicidality | I | Risk classification |
| OCI-R | 18 | OCD | I | Sum + 6 subscales |
| SSS-8 | 8 | Somatic symptoms | I | Sum (0-32) |
| DES-II | 28 | Dissociation | I | Mean (0-100%) |
| SCOFF | 5 | Eating disorders | I | Sum (0-5) |
| ISI | 7 | Insomnia | I | Sum (0-28) |
| PID-5-BF | 25 | Personality traits | II | 5 domains → HiTOP |
| WHODAS 2.0 | 12 | Functioning | IV | 6 ICF domains |

## Tech Stack

- **Diagnostic System UI**: Streamlit
- **Testcenter UI**: Flask + Bootstrap 5 + Jinja2
- **Decision Engine**: `transitions` (Hierarchical State Machine)
- **Visualization**: Plotly (PID-5 + HiTOP radar charts)
- **Data Storage**: SQLite (diagnostic codes + test sessions)
- **Internationalization**: Bilingual (German/English) via `translations.json` (661 keys per language)

## Installation

```bash
# Main diagnostic system
pip install streamlit plotly pandas transitions anytree

# Testcenter (separate)
pip install flask
```

## Usage

```bash
# Main diagnostic system (clinician interface)
streamlit run _data/multiaxial_diagnostic_system.py

# Testcenter (patient-facing + clinician admin)
python _data/testcenter/app.py
```

## Project Structure

```
paper/                                       # Scientific preprint (EN + DE + .bib)
_data/multiaxial_diagnostic_system.py        # Main application (V10, ~2850 lines)
_data/translations.json                      # Bilingual i18n (661 keys DE/EN)
_data/build_code_database.py                 # Diagnostic code database builder
_data/diagnostic_codes.db                    # Pre-built code database (ICD-11/DSM-5-TR/ICF)
_data/requirements.txt                       # Python dependencies
_data/testcenter/                            # Diagnostic Testcenter (Flask web app)
    app.py                                   #   Main application
    scoring.py                               #   Scoring engine (9 methods)
    config.py                                #   Configuration
    tests/                                   #   16 test definitions (JSON, bilingual)
    templates/                               #   HTML templates (Bootstrap 5)
    static/                                  #   CSS + JavaScript
_results/Konzept_Dimensionale_Integration.md # Dimensional integration concept (DE)
_results/Ausbauplan_Prototyp_V9.md           # Development roadmap (DE)
```

## Development Roadmap

See [Ausbauplan_Prototyp_V9.md](_results/Ausbauplan_Prototyp_V9.md) for the full roadmap.

**Completed (Sprint 1 / V9 + V9.1):**
- Ii/Ij swap (coverage before investigation)
- HiTOP spectra from Cross-Cutting data
- Symmetric Axis III (13 sub-axes)
- PRO/CONTRA evidence evaluation with confidence
- Formal + quantitative coverage analysis with metrics
- Prioritized investigation plan (3-tier)
- CAVE pattern-based notifications
- Longitudinal symptom timeline
- Extended medication form (IIIm)
- Full JSON export
- XSS protection (html escaping)
- WHODAS 2.0 domain score persistence
- GAF deprecation notice
- Professional-use disclaimer
- Full i18n coverage (no hardcoded strings)
- Robust Likert scale parsing

**Completed (Sprint 2 / V10):**
- Axis V P1-P4 structured coding (source axis + evidence level per factor)
- Pathophysiological causal model (genetic-neurobiological / psychological-developmental / environmental-situational)
- Therapy resistance tracking (treatment attempts, response rates, switch reasons)
- CGI-S / CGI-I outcome parameters with longitudinal tracking
- Session auto-save / data persistence (JSON-based save & load)

**Completed (Sprint 3 / V10.1 -- Testcenter):**
- Diagnostic Testcenter: standalone Flask web app with 16 validated instruments
- Bilingual test definitions (DE/EN) with complete item content and scoring
- Test batteries: multiple tests as a single client link
- Print-friendly output for pen & paper administration
- Automatic scoring with 9 scoring methods (sum, mean, algorithm, classification, etc.)
- REST API for programmatic integration
- Cross-Cutting → Testcenter integration (Gate 5 links to recommended instruments)
- Session management with token-based link sharing and deletion

**Next (Sprint 4):**
- Multi-professional role model (login/role-based axis access)
- Automated coverage analysis (cross-cutting to diagnosis mapping)
- Comorbidity rules (automated warnings)
- HSM disorder modules (11 structured modules)

## Citation

If you use this system in your research, please cite:

```bibtex
@article{geiger2026multiaxial,
  title={An Integrated Multiaxial Model for Computer-Assisted Psychiatric Diagnosis},
  author={Geiger, Lukas},
  year={2026},
  doi={10.5281/zenodo.18736725},
  publisher={Zenodo}
}
```

## License

- **Software** (code, templates, scoring engine): [MIT License](LICENSE)
- **Scientific papers** (`paper/`): [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Test instruments** (`_data/testcenter/tests/`): Each instrument under its original license (Public Domain, WHO, APA, etc.) -- see [`_data/testcenter/NOTICE.md`](_data/testcenter/NOTICE.md)

## Author

**Lukas Geiger** -- Independent Researcher, Bernau im Schwarzwald, Germany

*AI-assisted development: Claude Opus 4.6 (Anthropic), Gemini (Google DeepMind), Copilot (Microsoft)*

> ⚠️ **Rechtlicher Hinweis / Legal Notice**
>
> Dieses Projekt ist **kein Medizinprodukt** im Sinne der MDR (EU) 2017/745 / IVDR (EU) 2017/746. Es ist **nicht klinisch validiert**, **nicht durch BfArM oder eine Benannte Stelle geprüft**, **nicht zertifiziert**. Es verarbeitet Daten ausschließlich zu Forschungs- und Softwareentwicklungszwecken. Eine klinische oder diagnostische Nutzung ist ausdrücklich **nicht** die Zweckbestimmung. Entscheidungen über Diagnose und Therapie bleiben qualifizierten Fachpersonen vorbehalten.
>
> This project is **not a medical device** within the meaning of MDR (EU) 2017/745 / IVDR (EU) 2017/746. It is **not clinically validated**, **not approved by BfArM or any Notified Body**, **not certified**. Data is processed exclusively for research and software development purposes. Clinical or diagnostic use is explicitly **not** the intended purpose. Decisions about diagnosis and therapy remain reserved for qualified professionals.
>
> Unentgeltliche Open-Source-Schenkung (§§ 516 ff. BGB). Haftung auf Vorsatz und grobe Fahrlässigkeit beschränkt (§ 521 BGB). Nutzung auf eigenes Risiko. / Unpaid open-source donation. Liability limited to intent and gross negligence. Use at own risk.

