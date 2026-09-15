# Fokus-Tracker

Ein Ding nach dem anderen. Erzwingt Single-Tasking zwischen Schule, Ski
und Finanzen — es kann immer nur eine Session gleichzeitig laufen.

## Nutzung

```
python3 fokus.py start schule 25      # 25-Min-Session, Tag "schule"
python3 fokus.py stop                 # laufende Session vorzeitig beenden
python3 fokus.py today                # Sessions von heute
python3 fokus.py stats --days 7       # Auswertung ueber Zeitraum
```

Tags: `schule`, `ski`, `finanzen`, `sonstiges`.

## Warum

Ziel: Fokus verbessern statt alles gleichzeitig machen. Das Tool
blockt eine zweite Session, solange eine laeuft, und loggt jede
Session lokal (`data/sessions.jsonl`, nicht Teil des Repos), damit du
schwarz auf weiss siehst, wo deine Zeit hingeht.

Keine Abhaengigkeiten, reines Python 3 (Standardbibliothek).
