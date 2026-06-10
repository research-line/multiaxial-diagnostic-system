# German Style Check -- 2026-06-01

## Projekt

- Projekt: Diagnostic / Multiaxiale Diagnostik
- Pfad: `C:\Users\User\OneDrive\.TOPICS\.RESEARCH\.LAB\.CLOSED\!!!PP__Diagnostic`
- GeprÃ¼fte Dateien:
  - `paper\Review_Multiaxiale_Diagnostik_v4_en.tex`
  - `paper\Review_Multiaxiale_Diagnostik_v4_ger.tex`
  - `paper\Review_Multiaxiale_Diagnostik_v4_ger.pdf`
  - `paper\Review_Multiaxiale_Diagnostik_v4_kombi.pdf`

## Auswahlgrund

Vor der Projektauswahl wurden `CHECKED-REGISTRY.md`, `CHECKS-LOG.txt`, die Automations-Memory, `GPT.md`, `CLAUDE.md`, `PUBLIKATIONSVERFAHREN.md` sowie die projektlokalen Steuerdateien gelesen. FÃ¼r `Diagnostic / Multiaxiale Diagnostik` lag zwar am 2026-05-28 bereits ein Design-Check des aktiven v4-Satzes vor, der letzte echte German-Style-Check betraf aber noch die v3-Fassung vom 2026-05-23. Der heutige Lauf war daher kein Doppelcheck, sondern ein fÃ¤lliger Stil- und Terminologiepass der aktuellen deutschen Leitfassung.

## Kurzurteil

Die deutsche v4-Fassung ist fachlich nah an der englischen Leitversion und bereits insgesamt gut lesbar. Die klaren Restprobleme lagen nicht bei falschen KernÃ¼bersetzungen, sondern bei vereinzelten Hybridbegriffen, unnÃ¶tigem Meta-Englisch und einzelnen Formulierungen, die im Deutschen weniger wissenschaftlich-prÃ¤zise wirkten als nÃ¶tig.

## Sofort korrigiert

- `longitudinales Symptomtracking` -> `longitudinale Symptomverlaufsdokumentation`
- `Longitudinales Tracking` -> `Symptomverlauf`
- `CAVE-Alerts` / `regelbasierte Alerts` -> `CAVE-Warnhinweise` / `regelbasierte Warnhinweise`
- `Jeder Alert referenziert ...` -> `Jeder Warnhinweis verweist ...`
- `Response/Non-Response/Partial Response` -> `Ansprechen/kein Ansprechen/partielles Ansprechen`
- `Roadmap` -> `strategischen Fahrplan`
- `Experten-Review` / `Review` -> `Expertenbegutachtung` / `Begutachtung`
- `Time-on-Task` / `Time-on-Task-Analyse` -> `Bearbeitungszeit` / `Bearbeitungszeitanalyse`
- `umfassendes Assessment` -> `umfassende diagnostische Erhebung`

## Bewusst stehen gelassen

Die folgenden Begriffe wurden nicht still eingedeutscht, weil sie im Text als offizielle Instrumenten- oder Fachlabels fungieren oder als internationale Fachsprache noch gut vertretbar sind:

- `Cross-Cutting`
- `Cultural Formulation Interview`
- `Rapid Assessment`
- `Ecological Momentary Assessment`
- `Digital Phenotyping`
- `Implementation Science`
- `Shared Decision Making`
- `Routine Outcome Monitoring`
- `WHODAS 2.0`, `PID-5`, `HL7 FHIR`

Ein spÃ¤terer Journal-Feinschliff kann diese Gruppe bei Bedarf noch systematischer harmonisieren, aber sie war fÃ¼r diesen Lauf nicht eindeutig genug fÃ¼r Sofortkorrekturen.

## Verifikation

- `Review_Multiaxiale_Diagnostik_v4_ger.tex` seriell mit `pdflatex -interaction=nonstopmode -halt-on-error` neu gebaut.
- `Review_Multiaxiale_Diagnostik_v4_kombi.pdf` anschlieÃŸend aus aktueller EN- und frischer GER-PDF per `pypdf` neu gemergt.
- Harter Logscan ohne `LaTeX Error`, `Undefined control sequence`, undefinierte Zitate/Referenzen, `Fatal error`, `Emergency stop` oder `Overfull`-Treffer. Verblieben sind nur harmlose `Underfull \hbox`-Hinweise.
- `pdftotext -enc UTF-8` bestÃ¤tigt echte Umlaute in der deutschen PDF-Textspur und in der Kombi-PDF, u. a.:
  - `Symptomverlaufsdokumentation`
  - `strategischen Fahrplan`
  - `CAVE-Warnhinweise`
  - `Bearbeitungszeit`
  - `Ansprechen/kein Ansprechen/partielles Ansprechen`
- SHA256:
  - GER: `BD488D4A33EFB6FC6C71EAEF99BC31B1EED0F5DBF93B71AF409FAB062FB9AB99`
  - Kombi: `EB5343323DA21D843DAEF2A35647CBD6585986375E4F92C08C3EC3EE43EEF069`

## Restnotiz

Der heutige Lauf beseitigt die klaren Denglisch- und Stilreste der deutschen v4-Leitfassung. FÃ¼r einen spÃ¤teren optionalen Journal-Feinschliff bleiben vor allem die bewusst beibehaltenen internationalen Fachlabels relevant; sachliche Ãœbersetzungsfehler zwischen EN und DE wurden in den geprÃ¼ften Kernstellen nicht gefunden.
