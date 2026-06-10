# German Style Check -- 2026-05-23

## Projekt

- Projekt: Diagnostic / Multiaxiale Diagnostik
- Pfad: `C:\Users\User\OneDrive\.TOPICS\.RESEARCH\.LAB\.CLOSED\!!!PP__Diagnostic`
- GeprÃ¼fte Dateien:
  - `paper\Review_Multiaxiale_Diagnostik_v3_en.tex`
  - `paper\Review_Multiaxiale_Diagnostik_v3_ger.tex`
  - `paper\Review_Multiaxiale_Diagnostik_v3_ger.pdf`
  - `paper\Review_Multiaxiale_Diagnostik_v3_kombi.pdf`

## Auswahlgrund

FÃ¼r den aktuellen v3-Dateisatz war im zentralen Register bereits ein Zitations-, Design-, LLM-Muster- und GitHub-Check dokumentiert, aber noch kein eigener German Style Check. Zugleich wurde der deutsche Satz am 2026-05-22 nochmals neu gebaut.

## Kurzurteil

Die deutsche Fassung ist inhaltlich nah an der englischen Version und fachsprachlich insgesamt tragfÃ¤hig. Die klaren Schwachstellen lagen nicht bei groben FehlÃ¼bersetzungen des Kerninhalts, sondern bei verstreuten Hybridformulierungen, unnÃ¶tigem Denglisch, einer grammatisch defekten Gatekeeper-Stelle und einer kleinen internen Inkonsistenz im Forschungsbedarfsabschnitt.

## Sofort korrigiert

- PDF-Metadaten sprachlich und formal bereinigt:
  - `pdftitle`/`pdfsubject`/`pdfkeywords` jetzt mit echten Umlauten.
  - `Design-Paper` zu `Designpapier`.
- Terminologie und Stil geglÃ¤ttet:
  - `multi-professionell` -> `multiprofessionell`
  - `Bericht als Snapshot` -> `Bericht als Momentaufnahme`
  - `Paper` -> je nach Kontext `Artikel`, `Manuskript`
  - `Ground-Truth-Instanzen` -> `Referenzinstanzen`
  - `Goldstandard-Framework` -> `Goldstandard-Rahmen`
- Klare Denglisch-Stellen im Text beseitigt:
  - `triggern` -> `auslÃ¶sen`
  - `Alignment` -> `Abgleich`
  - `Framework` in der Gatekeeper-Tabelle/Passage durch deutsche Bezeichnungen ersetzt
  - `gemappt`/`Mapping` -> `zugeordnet`/`Zuordnung`
  - `visuell distinct` -> `visuell klar ... abgesetzt`
  - `Informed Consent` -> `Informierte Einwilligung`
  - `Illustrative Fallvignette` -> `Beispielhafte Fallvignette`
- Grammatik und Logik:
  - Gatekeeper-Schwellenlogik grammatisch repariert (`den klinischen Imperativ`).
  - Forschungsbedarfsabschnitt korrigiert: Es werden vier statt drei Forschungsrichtungen aufgezÃ¤hlt.

## Bewusst englisch belassen

Die folgenden Begriffe wurden nicht pauschal eingedeutscht, weil sie im Kontext als etablierte Fachlabels, offizielle Bezeichnungen oder sinnvolle Erstnennungen fungieren:

- `Cultural Formulation`
- `Cross-Cutting`
- `HiTOP`
- `RDoC`
- `HL7 FHIR`
- `Open-Source`
- `Rapid Assessment`
- `Digital Phenotyping`
- `Implementation Science`
- `Learning Health System`

Hier wÃ¤re nur bei einer bewussten Redaktionsentscheidung ein weiterer Vereinheitlichungspass sinnvoll, nicht als Sofortkorrektur.

## Ãœbersetzungsbefund EN -> DE

- Kein Hinweis darauf, dass zentrale Claims im Deutschen systematisch hÃ¤rter oder weicher formuliert wÃ¤ren als im Englischen.
- Die Hauptlogik der EN-Fassung bleibt in den geprÃ¼ften Kernabschnitten erhalten:
  - Abstract
  - Methodik
  - Gatekeeper-Logik
  - Abdeckungsanalyse
  - HiTOP/RDoC-Integration
  - Limitationen und Forschungsbedarf
- Die Korrekturen betreffen daher primÃ¤r sprachliche Form, Terminologiekonsistenz und Lesbarkeit, nicht den sachlichen Gehalt.

## Verifikation

- `Review_Multiaxiale_Diagnostik_v3_ger.tex` zweimal mit `pdflatex -interaction=nonstopmode -halt-on-error` gebaut.
- `Review_Multiaxiale_Diagnostik_v3_kombi.pdf` anschlieÃŸend in bestehender Reihenfolge EN -> DE per `pypdf` neu gemergt.
- `pdftotext -enc UTF-8` bestÃ¤tigt echte Umlaute in der deutschen Textspur, u. a.:
  - `computergestÃ¼tzten`
  - `EntscheidungsunterstÃ¼tzungssystem`
  - `Zusammenfassung`
  - `Beispielhafte Fallvignette`
  - `multiprofessionelle Zusammenarbeit`
- Windows-/PowerShell-`pdfinfo` zeigt UTF-8-Metadaten lokal mojibake-haft an; die extrahierte Textspur bestÃ¤tigt jedoch den korrekten Umlautstand im PDF.
- SHA256:
  - GER: `A06D17E3CE60C2AD291CAB5252D8446CFCA464CDA74C5A498CE98827B9901867`
  - Kombi: `576ED0CFB2C7215B7E5CD2DAA6A215BBB78FF464D14C45E4EF9AF52CE797B0E0`

## Restnotiz

Ein spÃ¤terer optionaler Stilpass kÃ¶nnte noch entscheiden, ob programmatiche und digital-health-nahe Labels wie `Rapid Assessment`, `Digital Phenotyping` oder `Learning Health System` im Deutschen stÃ¤rker geglÃ¤ttet oder bewusst als internationale Fachbegriffe gefÃ¼hrt werden sollen. FÃ¼r den jetzigen Lauf waren sie nicht eindeutig genug fÃ¼r eine Sofortkorrektur.
