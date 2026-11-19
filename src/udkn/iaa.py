"""
Inter-annotator agreement between two annotations of the same sentences.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from .conllu import Sentence
from .evaluate import align, feats_key, universal

def cohen_kappa(a: list, b: list) -> float:
    """Calculate Cohen kappa for two given lists."""
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in ca) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)

def agreement(a: list[Sentence], b: list[Sentence], strict: bool = True):
    """Returns (summary dict, list of disagreement rows for adjudication)."""
    pairs, skipped = align(a, b, strict)
    up_a, up_b, dr_a, dr_b = [], [], [], []
    n = head = las = feats = lemma = 0
    rows = []
    for sa, sb in pairs:
        for x, y in zip(sa.words, sb.words):
            n += 1
            up_a.append(x.upos); up_b.append(y.upos)
            dr_a.append(universal(x.deprel)); dr_b.append(universal(y.deprel))
            head += x.head == y.head
            las += x.head == y.head and universal(x.deprel) == universal(y.deprel)
            feats += feats_key(x.feats) == feats_key(y.feats)
            lemma += x.lemma == y.lemma
            for field_, v1, v2 in (("lemma", x.lemma, y.lemma), ("upos", x.upos, y.upos),
                                   ("feats", feats_key(x.feats), feats_key(y.feats)),
                                   ("head", x.head, y.head), ("deprel", x.deprel, y.deprel)):
                if v1 != v2:
                    rows.append({"sent_id": sa.sent_id, "tok": x.id, "form": x.form,
                                "field": field_, "annotator_A": v1, "annotator_B": v2})
    pct = lambda v: round(100 * v / n, 2) if n else 0.0
    summary = {"sentences": len(pairs), "words": n, "skipped_sentences": skipped, 
               "UPOS_agree": pct(sum(p == q for p, q in zip(up_a, up_b))),
               "UPOS_kappa": round(cohen_kappa(up_a, up_b), 4),
               "deprel_kappa": round(cohen_kappa(dr_a, dr_b), 4),
               "head_agree(UAS)": pct(head), "LAS_agree": pct(las),
               "feats_agree": pct(feats), "lemma_agree": pct(lemma)}
    return summary, rows

def write_disagreements(rows: list[dict], path: str | Path) -> None:
    """Write Inter-Annotator Agreement to file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cols = ["sent_id", "tok", "form", "field", "annotator_A", "annotator_B"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows()