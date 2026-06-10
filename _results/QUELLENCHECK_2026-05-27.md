# Quellencheck 2026-05-27 -- Multiaxiale Diagnostik

## Auswahlgrund

`!!!PP__Diagnostic` wurde gewÃ¤hlt, obwohl es am 2026-05-26 einen ORCID-/DOI-Sync-Check hatte, weil der letzte echte Quellencheck der Paperbibliographie vom 2026-05-01 stammte. Die spÃ¤teren LÃ¤ufe betrafen Health, Zitation, Stil, Disclosure und Metadaten. Da Zenodo v5.0 live ist und lokal ein v6.0-Kandidat offen liegt, waren bibliographische Fehler uploadrelevant.

## GeprÃ¼fte Quellen

- arXiv API: `https://export.arxiv.org/api/query?id_list=2602.12871`
- Crossref API/DOI: `https://doi.org/10.1017/S0033291722001301`
- Crossref API/DOI: `https://doi.org/10.3389/fpsyt.2021.643270`
- Crossref API/DOI: `https://doi.org/10.1080/10503307.2023.2181114`
- Crossref API/DOI: `https://doi.org/10.1186/s12888-023-05201-0`
- NCBI/PubMed ESearch DOI-Abgleich: PMIDs `34122175`, `35650658`, `30967483`, `36931228`, `37784115`

## Befund

- `MentalBench2024` war weiter falsch: arXiv `2602.12871` fÃ¼hrt den Titel `MentalBench: A DSM-Grounded Benchmark for Evaluating Psychiatric Diagnostic Capability of Large Language Models` und die Autoren Hoyun Song, Migyeong Kang, Jisu Shin et al., nicht Shen/Yang/Dong.
- `Kotov2022` hatte die richtige Arbeit, aber eine falsche Kurzautorengruppe. Crossref nennt Roman Kotov, David C. Cicero, Christopher C. Conway et al. sowie DOI `10.1017/S0033291722001301`.
- `Zimmermann2021` war dem falschen Erstautor zugeordnet. Die Frontiers-Publikation ist von Karel D. Riegel, Albert J. Ksinan und Lucia Schlosserova, DOI `10.3389/fpsyt.2021.643270`.
- Gegenproben zu Barkham 2023, Levis 2019 und Stasiak 2023 bestÃ¤tigten die im v3-Quellencheck bereits gesetzten DOI-/Journaldaten; dort war keine neue Ã„nderung nÃ¶tig.

## Korrektur

- Neue aktive Paperversion angelegt: `Review_Multiaxiale_Diagnostik_v4_en.tex`, `Review_Multiaxiale_Diagnostik_v4_ger.tex`, EN/GER/Kombi-PDF.
- Alter aktiver v3-Dateisatz archiviert unter `paper/_archive/2026-05-27_v3_pre_quellencheck/`.
- Citation-Keys aktualisiert:
  - `MentalBench2024` -> `Song2026MentalBench`
  - `Zimmermann2021` -> `Riegel2021`
- Bibliographie in EN und GER korrigiert:
  - MentalBench-Autoren/Titel/arXiv-DOI
  - HiTOP-2022-Autoren und DOI
  - PID5BF+M-Czech-Sample-Autoren und DOI

## Verifikation

- EN und GER mit `pdflatex -interaction=nonstopmode -halt-on-error` bis zum stabilen Log gebaut.
- Citation-Audit: EN/GER je 61 eindeutige Cite-Keys und 61 Bibitems; keine fehlenden oder unzitierten Keys.
- Harter Logscan: keine LaTeX-Fehler, undefinierten Referenzen/Zitate, Rerun-Blocker, Overfull-HBoxen oder Fatal Errors.
- Seiten: EN 43, GER 46, Kombi 89.
- SHA256:
  - EN `4F3223073C135CCF3451C843A4C5CC452706340C387614C561E9C674D5672387`
  - GER `F2059EA88D8EC28283C46683617AE738FDBD43915C0A12AD096A38062EC83A55`
  - Kombi `2B707052CCAD5C9FC1DEF1D1798DE8AB3F18145419B9DC74594CFC8CF8032E0E`
- Deutsche PDF-Textspur per `pdftotext -enc UTF-8` geprÃ¼ft: echte Umlaute und `ÃŸ` vorhanden, kein Mojibake.
- Zenodo-Dry-Run mit `--new-version 19073268 --version 6.0 --no-compile --abstract-from-plan --dry-run`: drei v4-PDFs gefunden; bekannter Resource-Type-Hinweis bleibt `publication/preprint` statt live `software`.

## Folge

Da Zenodo v5.0 bereits live ist (`10.5281/zenodo.19073268`), ist ein neuer Zenodo-v6.0-Upload notwendig. Der Upload muss den v4-Dateisatz verwenden und vor AusfÃ¼hrung weiterhin die offene Resource-Type-Entscheidung klÃ¤ren: live ist `software`, historischer Dry-Run meldete `publication/preprint`.
