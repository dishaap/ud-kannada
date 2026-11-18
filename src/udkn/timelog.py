"""Tiny annotation time log to measure annotation time."""
from __future__ import annotations

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

PHASES = ("scratch", "correct", "review") # annotate from scratch / correct pre-annotation / second-pass review
FIELDS = ["date", "annotator", "batch", "phase", "sentences", "minutes"]

def add(path: str | Path, annotator: str, batch: str, phase: str, sentences: int, minutes: float) -> None:
    """Write annotation log to file."""
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({"date": dt.date.today().isoformat(), "annotator": annotator, "batch": batch,
                    "phase": phase, "sentences": sentences, "minutes": minutes})

def summary(path: str | Path, budget_hours: float = 300, annotation_share: float = 0.6) -> str:
    """Create summary of annotation logs including time left in annotation budget, sentences left to annotate, 
    correct annotations."""
    path = Path(path)
    if not path.exists():
        return "no time log yet"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    per = defaultdict(lambda: [0, 0.0])
    for r in rows:
        k = (r["phase"], r["batch"])
        per[k][0] += int(r["sentences"]); per[k][1] += float(r["minutes"])
    out = ["phase     batch     sents  minutes  sents/hour"]
    for (ph, b), (s, m) in sorted(per.items()):
        out.append(f"{ph:9s} {b:9s} {s:5d}  {m:7.0f}  {60 * s / m if m else 0:9.1f}")
    tot_m = sum(v[1] for v in per.values())
    corr = [(s, m) for (ph, _), (s, m) in per.items() if ph == "correct"]
    if corr and sum(m for _, m in corr):
        rate = 60 * sum(s for s, _ in corr) / sum(m for _, m in corr)
        left  = max(budget_hours - tot_m / 60, 0) * annotation_share
        out.append(f"correction speed {rate:.1f} sents/h -> ~{rate * left:.0f} more sentences "
                   f"if {annotation_share:.0%} of the remaining hours go to correction")
    return "n".join(out)
