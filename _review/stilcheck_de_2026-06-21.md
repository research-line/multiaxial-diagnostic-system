# German Style Check -- 2026-06-21

## Projekt

- Projekt: Diagnostic / Multiaxiale Diagnostik
- Pfad: `C:\Users\User\OneDrive\.TOPICS\.RESEARCH\.LAB\.CLOSED\!!!PP__Diagnostic`
- GeprÃ¼fte Dateien:
  - `paper\Review_Multiaxiale_Diagnostik_v4_ger.tex`
  - `paper\Review_Multiaxiale_Diagnostik_v4_ger.pdf`
  - `paper\Review_Multiaxiale_Diagnostik_v4_kombi.pdf`

## Auswahlgrund

Vor der Projektauswahl wurden `CHECKED-REGISTRY.md`, `CHECKS-LOG.txt`, `CLAUDE.md`, `STATUS_UEBERSICHT.md` sowie die projektlokalen Steuerdateien gelesen. FÃ¼r das Projekt `Diagnostic / Multiaxiale Diagnostik` fand zwar kÃ¼rzlich ein GitHub-Repo-Check (2026-06-21) und ein Daten-/Strukturdesign-Check (2026-06-12) statt, der letzte German-Style-Check lag jedoch mit dem 2026-06-01 bereits 20 Tage zurÃ¼ck. Am 17.06.2026 wurden neue Validierungs-Gate-Ledger-Tabellen in das v4-Manuskript integriert (synchrone Publikation per Commit `8f46b03` am 21.06.2026). Der heutige Lauf prÃ¼ft und glÃ¤ttet diese neu hinzugefÃ¼gten Textpassagen systematisch und beseitigt dort verbliebenes Denglisch sowie Hybridbegriffe.

## Kurzurteil

Die am 17.06.2026 neu hinzugefÃ¼gte Tabelle `tab:validierungs-gate-ledger` fÃ¼hrte eine Reihe englischer Fachbegriffe in den deutschen Text ein (wie "Diagnostic Reasoning Ledger", "Audit-Log", "Mapping", "Leakage-PrÃ¼fung"). Diese wurden im Sinne eines prÃ¤zisen, klaren deutschen Wissenschaftsstils harmonisiert. Gleichzeitig wurden vereinzelte verbliebene Anglizismen im Haupttext ("Literaturreview", "Framework", "Trait-Assessments" samt Grammatikfehlern) korrigiert. Die fachliche IntegritÃ¤t und die Konsistenz zum englischen Begleitdokument bleiben vollstÃ¤ndig gewahrt.

## Sofort korrigiert

### Haupttext
- `Literaturreview` -> `Literatur\"ubersicht` (Zeile 123, methodischer Kontext)
- `multiaxiale Framework ... biopsychosoziales Framework` -> `multiaxiale Klassifikationssystem ... biopsychosoziales Rahmenmodell` (Zeile 180)
- `Integration des dimensionalen Trait-Assessments` -> `Integration der dimensionalen Trait-Diagnostik` (Zeile 345, inklusive Grammatikkorrektur: Genitiv-Artikel von Maskulinum auf Femininum angepasst)

### Tabelle: Validierungs-Gate-Ledger (Zeilen 1147-1152)
- **Gate-Bezeichnungen:**
  - `Diagnostic Reasoning Ledger` -> `Diagnostisches Herleitungs-Ledger`
  - `Consultation Evidence-Gathering Gate` -> `Konsultations-Evidenzerhebungs-Gate`
  - `Synthetic-Fidelity-/Fairness-Gate` -> `Synthetik-Fidelity-/Fairness-Gate`
  - `AI-Agent-Governance-Gate` -> `KI-Agenten-Governance-Gate`
  - `ICD-Coding-Boundary` -> `ICD-Codierungsgrenze`
  - `Achse-VI-Biomarker-Queue` -> `Achse-VI-Biomarker-Warteschlange`
- **Tabelleninhalte (Denglisch-GlÃ¤ttung):**
  - `Review-Notizen` -> `Gutachter-Notizen` (Konsistenz zum vorherigen Review-Verbot von "Review")
  - `Expertenreview` -> `Expertenbegutachtung`
  - `Reasoning-Qualit\"at` -> `Entscheidungsqualit\"at`
  - `Audit-Log` -> `Pr\"ufprotokoll`
  - `Monitoringplan` -> `\"Uberwachungsplan`
  - `Mapping von klinischer Entscheidung` -> `Zuordnung der klinischen Entscheidung`
  - `Leakage-Pr\"ufung` -> `Informationsabfluss-Pr\"ufung`

## Bewusst stehen gelassen

- `Backing` (Toulmin-Argumentationstheorie, als etablierter Fachbegriff belassen)
- `Human-in-the-loop-Punkt` (internationaler Standardbegriff der KI-Governance)
- `Wearable-, Stimm-, EMA- oder Chronosignale` (klinische AbkÃ¼rzungen und Fachbezeichnungen wie Ecological Momentary Assessment)

## Verifikation

- `Review_Multiaxiale_Diagnostik_v4_ger.tex` erfolgreich mittels `pdflatex` (MiKTeX 25.12) im Nonstopmode ohne Fehler neu kompiliert.
- `Review_Multiaxiale_Diagnostik_v4_kombi.pdf` mit `build_kombi_pdf.py` neu aus der aktuellen EN- und der neu kompilierten GER-PDF generiert.
- Textspur verifiziert: Alle Umlaute werden im PDF als echte Umlaute gerendert (Ã¤, Ã¶, Ã¼, ÃŸ).

## SHA256-Hashes

```
EA403A23DFBCCD5E3C1DEA3E224C8937DBDD9F297076C8D9F723ED848CC121F7  paper/Review_Multiaxiale_Diagnostik_v4_ger.tex
91C47F16E6B9C252C5395A2D57161663F5B002A9D61040CDD8264B71482B78A6  paper/Review_Multiaxiale_Diagnostik_v4_ger.pdf
1DE474D796649C6FDD6348458028763973FC2F723DCB49B6383F7B995F342BF8  paper/Review_Multiaxiale_Diagnostik_v4_kombi.pdf
```
