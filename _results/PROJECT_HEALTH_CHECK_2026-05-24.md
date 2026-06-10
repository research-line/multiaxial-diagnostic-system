# Project Health Check -- 2026-05-24

Projekt: Diagnostic / Multiaxiale Diagnostik
Pfad: `.LAB/.CLOSED/!!!PP__Diagnostic/`
Automation: `research-project-health`

## Auswahlgrund

Der letzte echte Projekt-Health-Check lag auf 2026-05-01. Danach gab es zwar Spezialchecks (Testcenter-Quellen, LLM-Muster, Zitation, English Style), aber keinen erneuten Live-Abgleich des v6.0-Zenodo-Gates.

## Zenodo Live

Quelle: `https://zenodo.org/api/records/19073268` und Versionsendpoint.

- Latest Record: `19073268`
- DOI: `10.5281/zenodo.19073268`
- Concept: `10.5281/zenodo.18736725`
- Version: `5.0`
- Ã–ffentliche Versionen: fÃ¼nf (`1.0` bis `5.0`)
- Resource-Type: `software`
- Sprache: `eng`
- Lizenz: `cc-by-4.0`
- Live-Dateien:
  - `Review_Multiaxiale_Diagnostik_v2_en.pdf`, MD5 `213c5103d1b365a5465a6161894688fd`
  - `Review_Multiaxiale_Diagnostik_v2_ger.pdf`, MD5 `d9921b4c912447edba1412281577ef20`

## Befund

- Zenodo ist unverÃ¤ndert v5.0; kein neuer Upload wurde ausgefÃ¼hrt.
- Der Live-Record ist weiterhin als Software klassifiziert. Das sollte bei v6.0 erhalten bleiben, sofern kein bewusster Wechsel auf Preprint entschieden wird.
- Die API zeigt fehlende Creator-ORCID/Affiliation und ein kontaminiertes Keyword-Feld (`... Uploads: ...`). `ZENODO_CREDENTIALS.md` enthÃ¤lt jetzt die sauberen Zielwerte fÃ¼r v6.0.
- Der lokale v6.0-Kandidat ist neuer als live, weil er Quellen-, Disclosure-, Zitations- und Style-Fixes enthÃ¤lt.

## Lokaler v6.0-Kandidat

- EN PDF: MD5 `ff1aa533f557ae784ce5d0e93c242aba`, SHA256 `7806FDC25AF1A2A8AFFC97C934C163B9F6AD224338F7330FC75DF35AB42B7D26`
- GER PDF: MD5 `cbfe640422fb8f74b68baef519bebeb3`, SHA256 `E622E4CB2179B54885D56EE89584BC0EEE76E6D1CF7B8A689D2024C414A79FA8`
- Kombi PDF: MD5 `078bc0549adfb3d71a46b6858a8c1dd7`, SHA256 `16FAFD2D9D5AD3FD62C875276BE93FA085E186EDEAE4203EEC4E2B3BC45BAB32`
- Seiten: EN 43, GER 46, Kombi 89

## Aktualisiert

- `ZENODO_CREDENTIALS.md`: Live-Abgleich auf 2026-05-24, ORCID/Affiliation, frische MD5/SHA256, `.LAB`-Uploadpfad, Software-Beibehalten-Empfehlung.
- `AKTIONSPLAN.md`: neuer Health-Check-Status und Logeintrag.
- `TODO.md`: neuer Health-Check-Block mit offener Resource-Type-Entscheidung.
- Alte `paper/compile_*.log`-ZwischenlÃ¤ufe entfernt, weil sie Ã¼berholte Erstpass-Warnungen enthielten und den `paper_publisher.py`-Dry-Run blockierten; die finalen `Review_Multiaxiale_Diagnostik_v3_*.log` bleiben erhalten.

## Offen

- User-Freigabe fÃ¼r v6.0.
- Resource-Type-Entscheidung vor Upload; Empfehlung: `software` beibehalten.
- Dry-Run 2026-05-24 findet drei PDFs, meldet aber weiterhin `publication/preprint` und `Abstract DE: (nicht verfÃ¼gbar)`. Falls v6.0 als Software erhalten bleiben soll, vorher Toolverhalten patchen oder Zenodo-UI/API verwenden.
