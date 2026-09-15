#!/usr/bin/env python3
"""Fokus-Tracker: Ein Ding nach dem anderen.

Erzwingt Single-Tasking: es kann immer nur eine Session laufen
(Tags: schule, ski, finanzen, sonstiges). Jede Session wird geloggt,
damit du siehst, wo deine Zeit wirklich hingeht.

Nutzung:
    python3 fokus.py start schule 25      # startet 25-Min-Session, Tag "schule"
    python3 fokus.py stop                 # beendet laufende Session vorzeitig
    python3 fokus.py today                # Sessions von heute
    python3 fokus.py stats [--days N]     # Auswertung pro Tag, Standard 7 Tage
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
LOG_FILE = DATA_DIR / "sessions.jsonl"
LOCK_FILE = DATA_DIR / "active.json"

TAGS = ["schule", "ski", "finanzen", "sonstiges"]


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def load_lock():
    if LOCK_FILE.exists():
        return json.loads(LOCK_FILE.read_text())
    return None


def write_lock(data):
    LOCK_FILE.write_text(json.dumps(data))


def clear_lock():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def append_session(tag, planned_minutes, actual_minutes, completed):
    ensure_data_dir()
    entry = {
        "tag": tag,
        "planned_minutes": planned_minutes,
        "actual_minutes": round(actual_minutes, 1),
        "completed": completed,
        "started_at": None,
        "ended_at": datetime.now().isoformat(timespec="seconds"),
    }
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def cmd_start(args):
    if args.tag not in TAGS:
        print(f"Unbekannter Tag '{args.tag}'. Erlaubt: {', '.join(TAGS)}")
        sys.exit(1)

    active = load_lock()
    if active:
        print(
            f"Es laeuft schon eine Session: '{active['tag']}' seit "
            f"{active['started_at']}. Erst 'stop', dann neu starten."
        )
        print("Ein Ding nach dem anderen.")
        sys.exit(1)

    ensure_data_dir()
    started_at = datetime.now()
    write_lock(
        {
            "tag": args.tag,
            "planned_minutes": args.minutes,
            "started_at": started_at.isoformat(timespec="seconds"),
        }
    )

    print(f"Fokus-Session: {args.tag} | {args.minutes} Min")
    print("Ctrl+C zum vorzeitigen Beenden (wird trotzdem geloggt).")

    total_seconds = args.minutes * 60
    try:
        for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            print(f"\r  {mins:02d}:{secs:02d} verbleibend   ", end="", flush=True)
            time.sleep(1)
        print("\nFertig. Session abgeschlossen.")
        actual_minutes = args.minutes
        completed = True
    except KeyboardInterrupt:
        elapsed = (datetime.now() - started_at).total_seconds() / 60
        print(f"\nAbgebrochen nach {elapsed:.1f} Min.")
        actual_minutes = elapsed
        completed = False

    append_session(args.tag, args.minutes, actual_minutes, completed)
    clear_lock()


def cmd_stop(args):
    active = load_lock()
    if not active:
        print("Keine aktive Session.")
        return
    started_at = datetime.fromisoformat(active["started_at"])
    elapsed = (datetime.now() - started_at).total_seconds() / 60
    append_session(active["tag"], active["planned_minutes"], elapsed, False)
    clear_lock()
    print(f"Session '{active['tag']}' gestoppt nach {elapsed:.1f} Min.")


def read_sessions():
    if not LOG_FILE.exists():
        return []
    sessions = []
    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if line:
                sessions.append(json.loads(line))
    return sessions


def cmd_today(args):
    sessions = read_sessions()
    today = datetime.now().date()
    todays = [
        s for s in sessions
        if datetime.fromisoformat(s["ended_at"]).date() == today
    ]
    if not todays:
        print("Heute noch keine Session geloggt.")
        return
    total = 0
    for s in todays:
        mark = "OK" if s["completed"] else "abgebrochen"
        print(f"  {s['tag']:<10} {s['actual_minutes']:>5.1f} Min  ({mark})")
        total += s["actual_minutes"]
    print(f"  {'Summe':<10} {total:>5.1f} Min")


def cmd_stats(args):
    sessions = read_sessions()
    cutoff = datetime.now() - timedelta(days=args.days)
    recent = [
        s for s in sessions if datetime.fromisoformat(s["ended_at"]) >= cutoff
    ]
    if not recent:
        print(f"Keine Sessions in den letzten {args.days} Tagen.")
        return

    per_tag = {}
    for s in recent:
        per_tag.setdefault(s["tag"], {"minutes": 0.0, "count": 0})
        per_tag[s["tag"]]["minutes"] += s["actual_minutes"]
        per_tag[s["tag"]]["count"] += 1

    print(f"Auswertung letzte {args.days} Tage:")
    total_minutes = 0.0
    for tag, data in sorted(per_tag.items(), key=lambda x: -x[1]["minutes"]):
        hours = data["minutes"] / 60
        print(f"  {tag:<10} {data['minutes']:>6.1f} Min ({hours:.1f} h)  |  {data['count']} Sessions")
        total_minutes += data["minutes"]
    print(f"  {'Gesamt':<10} {total_minutes:>6.1f} Min ({total_minutes/60:.1f} h)")


def main():
    parser = argparse.ArgumentParser(description="Fokus-Tracker: ein Ding nach dem anderen.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Neue Fokus-Session starten")
    p_start.add_argument("tag", choices=TAGS)
    p_start.add_argument("minutes", type=int)
    p_start.set_defaults(func=cmd_start)

    p_stop = sub.add_parser("stop", help="Laufende Session vorzeitig beenden")
    p_stop.set_defaults(func=cmd_stop)

    p_today = sub.add_parser("today", help="Sessions von heute anzeigen")
    p_today.set_defaults(func=cmd_today)

    p_stats = sub.add_parser("stats", help="Auswertung ueber mehrere Tage")
    p_stats.add_argument("--days", type=int, default=7)
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
