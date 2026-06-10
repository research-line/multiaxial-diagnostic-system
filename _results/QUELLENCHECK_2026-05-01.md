# Quellencheck 2026-05-01 -- Diagnostic

## Umfang

GeprÃ¼ft wurden die 59 Inline-BibliographieeintrÃ¤ge der aktuellen EN/DE-LaTeX-Dateien. Die Datei `paper/diagnostic_references.bib` ist ergÃ¤nzend und nicht vollstÃ¤ndig kanonisch; maÃŸgeblich sind derzeit die Inline-`thebibliography`-BlÃ¶cke in `Review_Multiaxiale_Diagnostik_v3_en.tex` und `Review_Multiaxiale_Diagnostik_v3_ger.tex`.

## Recherchequellen

- Crossref REST API und DOI-AuflÃ¶sung
- NCBI/PubMed E-utilities
- Webrecherche zu nicht per DOI/PubMed eindeutig auffindbaren EintrÃ¤gen
- arXiv-Abgleich fÃ¼r MentalBench
- Zenodo/GitHub-Abgleich fÃ¼r Repository- und Upload-Kontext

## Korrekturen

- `AyusoMateos2010` war als einzelne ICF-Core-Set-Quelle nicht verifizierbar. Ersetzt durch drei verifizierbare ICF-Core-Set-Quellen zu Depression, Bipolar Disorders und Schizophrenia.
- `Huber2022` zu Routine Outcome Monitoring war nicht belastbar verifizierbar und wurde entfernt; ROM wird Ã¼ber Barkham et al. 2023 gestÃ¼tzt.
- `Barkham2023` korrigiert auf *Routine Outcome Monitoring (ROM) and Feedback: Research Review and Recommendations*, `Psychotherapy Research`, 33(7), 841-855, DOI `10.1080/10503307.2023.2181114`.
- `LindenBaron2005` korrigiert auf DOI `10.1055/s-2004-834786` und geprÃ¼fte Seiten `144-151`.
- `Probst2014` Titel korrigiert auf "Caught in the quest for a theory of mental disorder", DOI `10.1177/1049731513491326`.
- `BJPsychAdv2024` korrigiert auf Mayall et al. 2024, *Practical aspects of multiaxial classification*, DOI `10.1192/bja.2023.39`.
- `Aboraya2006` korrigiert auf `Psychiatry (Edgmont)` und PMID `21103149`.
- `Allison2012` Seiten korrigiert auf `202-212.e7`, DOI `10.1016/j.jaac.2011.11.003`.
- `Stasiak2023` um DOI `10.1186/s12888-023-05201-0` ergÃ¤nzt.
- GitHub-URL im Paper von `github.com/lukisch/...` auf `github.com/um-bruch/multiaxial-diagnostic-system` aktualisiert.

## Neue Paperdateien

- `paper/Review_Multiaxiale_Diagnostik_v3_en.tex` / `.pdf` -- 43 Seiten
- `paper/Review_Multiaxiale_Diagnostik_v3_ger.tex` / `.pdf` -- 46 Seiten
- `paper/Review_Multiaxiale_Diagnostik_v3_kombi.pdf` -- 89 Seiten

Die bisherigen v2-Artefakte wurden nach `_archive/quellencheck_2026-05-01_v2/` verschoben.

## Verifikation

LaTeX wurde fÃ¼r EN und DE mehrfach gebaut, anschlieÃŸend wurde die Kombi-PDF aus EN+DE erzeugt. Die finalen Logs enthalten keine undefinierten Zitate, keine undefinierten Referenzen und keine offenen "Rerun"-Warnungen. Es bleiben nur Layout-Warnungen aus bestehenden Tabellen/Boxen.

Da auf Zenodo bereits v5.0 live ist (`10.5281/zenodo.19073268`), ist nach User-Freigabe ein neuer Zenodo-v6.0-Upload mit den v3-Dateien nÃ¶tig.

Der anschlieÃŸende `paper_publisher.py --dry-run` findet die drei v3-PDFs korrekt. Offen bleibt die Resource-Type-Entscheidung: Zenodo v5.0 ist live als `Software` klassifiziert, der aktuelle Dry-Run meldet dagegen `publication/preprint`.
