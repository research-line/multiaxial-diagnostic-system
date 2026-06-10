# English Style Check -- 2026-05-23

Projekt: Diagnostic / Multiaxiale Diagnostik
Pfad: `.LAB/.CLOSED/!!!PP__Diagnostic/`
GeprÃ¼fte Leitfassung: `paper/Review_Multiaxiale_Diagnostik_v3_en.tex`

## Auswahlgrund

Der aktive v3-Dateisatz hatte im zentralen Register bereits Design-, Quellen-, Zitations-, LLM-Muster- und German-Style-Checks, aber noch keinen zentral registrierten English-Style-Check. Wegen des lokalen v6.0-Maintenance-Gates war ein claim-sensibler englischer Stilpass sinnvoll.

## Korrekturen

Die EN-Fassung wurde fachsprachlich geglÃ¤ttet, ohne neue Quellen oder neue wissenschaftliche Claims einzufÃ¼hren:

- `gold-standard framework` wurde zu `reference framework`.
- Rhetorische Formulierungen wie `The clinical community lost more than it gained` wurden neutralisiert.
- Ãœberstarke OriginalitÃ¤ts- und ObjektivitÃ¤tsformeln wurden zurÃ¼ckgenommen: `objective complement`, `direct operationalization`, `goes far beyond`, `exactly the same capabilities`, `directly supports`, `demonstrating robustness`, `best of`.
- Mehrere fachsprachlich unidiomatische Stellen wurden prÃ¤zisiert: `epistemological overall system`, `computer-assisted overall system`, `in a depth`, `offers in return`.
- Die finale Zusammenfassung wurde stÃ¤rker auf den tatsÃ¤chlichen Status als Designarchitektur mit ausstehender Expert Review, ReliabilitÃ¤tstestung und prospektiver Evaluation ausgerichtet.

## Verifikation

- EN/GER je zweimal mit `pdflatex -interaction=nonstopmode -halt-on-error` gebaut.
- Kombi-PDF aus EN+GER mit `pypdf` neu gemergt; Kombi-Metadaten mit echten Umlauten gesetzt.
- Seitenzahlen: EN 43 S., GER 46 S., Kombi 89 S.
- SHA256:
  - EN: `7806FDC25AF1A2A8AFFC97C934C163B9F6AD224338F7330FC75DF35AB42B7D26`
  - GER: `E622E4CB2179B54885D56EE89584BC0EEE76E6D1CF7B8A689D2024C414A79FA8`
  - Kombi: `16FAFD2D9D5AD3FD62C875276BE93FA085E186EDEAE4203EEC4E2B3BC45BAB32`
- Logscan ohne harte Treffer fÃ¼r LaTeX-Fehler, undefinierte Referenzen/Zitate, Rerun-Blocker, Overfull-Boxen oder Natbib-Warnungen.
- Deutsche PDF-Textspur geprÃ¼ft: echte Umlaute fÃ¼r `fÃ¼r`, `Ã¼ber`, `StÃ¶rung`, `AufklÃ¤rung`, `computergestÃ¼tzte`; Kombi-Metadaten enthalten `fÃ¼r` und `computergestÃ¼tzte`.

## Folgehinweis

Kein Zenodo-Upload und kein GitHub-Sync in diesem Lauf. FÃ¼r v6.0 bleiben die bestehenden Gates maÃŸgeblich: User-Freigabe und Resource-Type-Entscheidung.
