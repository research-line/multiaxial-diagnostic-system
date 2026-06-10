# ORCID-/DOI-Sync-Check -- 2026-05-26

Projekt: Diagnostic / Multiaxiale Diagnostik
Pfad: `.LAB/.CLOSED/!!!PP__Diagnostic/`
Automation: `research-orcid-doi-sync-check`

## Auswahlgrund

Genau ein Projekt mit vorhandener Zenodo-DOI wurde geprÃ¼ft. `!!!PP__Diagnostic` wurde bevorzugt, weil im frischen Root-Register noch kein eigener ORCID-/DOI-Sync-Lauf fÃ¼r dieses Projekt dokumentiert war und der letzte Live-Health-Check vom 2026-05-24 bereits konkrete MetadatenlÃ¼cken zeigte.

## GeprÃ¼fte Quellen

- Root: `PUBLIKATIONSVERFAHREN.md`, `STATUS_UEBERSICHT.md`, `SCIENTIFIC_WORK_NOTES.md`, `_templates/README.md`, `TODO.md`, `CHECKED-REGISTRY.md`, `CHECKS-LOG.txt`
- Projekt: `ZENODO_CREDENTIALS.md`, `AKTIONSPLAN.md`, `TODO.md`, `README.md`, `paper/Review_Multiaxiale_Diagnostik_v3_en.tex`, `paper/Review_Multiaxiale_Diagnostik_v3_ger.tex`
- Live: `https://zenodo.org/api/records/19073268`, `https://zenodo.org/api/records/18736725`
- ORCID Public API: `https://pub.orcid.org/v3.0/0009-0005-7296-1534/works`
- Lokale Tool-Konfiguration: `C:\Users\User\.config\paper_publisher\config.json`

## Befund

- Zenodo latest ist konsistent dokumentierbar: Record `19073268`, DOI `10.5281/zenodo.19073268`, Concept `10.5281/zenodo.18736725`, Version `5.0`, Status `published`, Resource-Type `software`, Sprache `eng`.
- Die Live-Metadaten bleiben unvollstÃ¤ndig: Creator-ORCID und Affiliation fehlen im API-Record, und das Keyword-Feld ist mit Upload-Text kontaminiert. Diese Punkte sind lokal bereits als v6-Zielwerte dokumentiert.
- Die Ã¶ffentliche ORCID-Works-API liefert weiterhin eine leere `group`-Liste. FÃ¼r Diagnostic ist damit aktuell kein Ã¶ffentlich sichtbarer Werkseintrag auf ORCID erkennbar.
- Lokaler authentifizierter ORCID-Abgleich war nicht mÃ¶glich: `ORCID_ID` ist gesetzt, aber `ORCID_ACCESS_TOKEN` fehlt.
- Im lokalen Manuskriptbestand gab es echten Statusdrift: EN und GER behaupteten noch, die Zenodo-Archivierung stehe aus. Dieser Drift wurde auf den tatsÃ¤chlich verÃ¶ffentlichten Stand korrigiert.

## Aktualisiert

- `ZENODO_CREDENTIALS.md`: Ã¶ffentlicher ORCID-Stand, lokale ORCID-Toollage und konkrete ORCID-AusfÃ¼llhilfe ergÃ¤nzt.
- `AKTIONSPLAN.md`: heutiger ORCID-/DOI-Sync-Befund und offener manueller ORCID-Schritt nachgezogen.
- `TODO.md`: neuer Aufgabenblock mit konkreter ORCID-Nachpflege angelegt.
- `paper/Review_Multiaxiale_Diagnostik_v3_en.tex`: Archivierungsabschnitt auf den bestehenden Zenodo-Software-Record mit Concept-DOI und latest DOI aktualisiert.
- `paper/Review_Multiaxiale_Diagnostik_v3_ger.tex`: dieselbe Statuskorrektur in der deutschen Fassung.

## Manuelle ORCID-AusfÃ¼llhilfe

- Werktyp: `software`
- Titel: `An Integrated Multiaxial Model for Computer-Assisted Psychiatric Diagnosis: Synthesis of DSM-5-TR, ICD-11, and ICF in a 6-Axis Expert System`
- Stabile DOI: `10.5281/zenodo.18736725`
- Latest DOI zum aktuellen Stand: `10.5281/zenodo.19073268`
- Aktuelle Version: `5.0`
- Kurznotiz fÃ¼r ORCID: Zenodo-Software-Record mit begleitendem EN/GER-Paperpaket; lokaler v6.0-Kandidat ist noch nicht verÃ¶ffentlicht.

## Verifikation

- Zenodo- und ORCID-Abfrage nur lesend.
- EN/GER nach der Statuskorrektur neu gebaut; Kombi-PDF neu gemergt.
- Harte Logsuche ohne `LaTeX Error`, `Undefined control sequence`, undefinierte `Citation`/`Reference`, `Overfull`, `Fatal error` oder `Emergency stop`.
- Deutsche Textspur mit echten Umlauten per `pdftotext -enc UTF-8` geprÃ¼ft.

## Offen

- Manuellen ORCID-Werkeintrag anlegen oder bestehenden privaten Eintrag auf Ã¶ffentlich stellen.
- Vor einem v6.0-Upload weiter offen: Resource-Type bewusst auf `software` halten oder den Wechsel zu `publication/preprint` explizit entscheiden.
