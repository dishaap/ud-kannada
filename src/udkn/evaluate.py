"""
Gold-vs-prediction scoring: UPOS, UFeats; Lemma, UAS, LAS, AllTags (+ per-UPOS breakdown). Adapted from dishaap/cogs-402.
"""
from __future__ import annotations

from collections import Counter

from .conllu import Sentence

class TokenizationMismatch(ValueError):
    pass

def feats_key(f: str) -> str:
    return "_" if f == "_" else "|".join(sorted(f.split("|")))

def universal(rel: str) -> str:
    return rel.split(":")[0]

def align(gold: list[Sentence], pred: list[Sentence], strict: bool = True):
    """Align gold-standard data to predicted data. strict = True -> tokenisation must be exactly the same in both sets."""
    if len(gold) != len(pred):
        raise ValueError(f"different number of sentences: {len(gold)} vs {len(pred)}")
    pairs, skipped = [], 0
    for g, p in zip(gold, pred):
        if g.sent_id and p.sent_id and g.sent_id != p.sent_id:
            raise ValueError(f"sentence order differs: {g.sent_id} vs {p.sent_id}")
        if [w.form for w in g.words] != [w.form for w in p.words]:
            if strict:
                raise TokenizationMismatch(f"tokenisation differs in {g.sent_id or '?'}")
            skipped += 1
            continue
        pairs.append((g, p))
    return pairs, skipped

def evaluate(gold: list[Sentence], pred: list[Sentence], strict: bool = True) ->  dict:
    """Evaluate gold-vs-prediction scoring for UPOS, UFeats, Lemma, UAS, LAS, AllTags etc, and return stats as dict."""
    pairs, skipped = align(gold, pred, strict)
    n = upos = feats = lemma = uas = las = las_full = alltags = 0
    per_gold: Counter = Counter()
    per_ok: Counter = Counter()
    conf: Counter = Counter()
    for g, p in pairs:
        for a, b in zip(g.words, p.words):
            n += 1
            ok_u, ok_f, ok_l = a.upos == b.upos, feats_key(a.feats) == feats_key(b.feats), a.lemma == b.lemma
            ok_h = a.head == b.head
            upos += ok_u; feats += ok_f; lemma += ok_l; uas += ok_h
            las += ok_h and universal(a.deprel) == universal(b.deprel)
            las_full += ok_h and a.deprel == b.deprel
            alltags += ok_u and ok_f and ok_l
            per_gold[a.upos] += 1
            per_ok[a.upos] += ok_u
            if not ok_u:
                conf[(a.upos, b.upos)] += 1
    pct = lambda x: round(100 * x / n, 2) if n else 0.0
    return {
        "sentences": len(pairs), "words": n, "skipped_sentences": skipped,
        "UPOS": pct(upos), "UFeats": pct(feats), "Lemma": pct(lemma),
        "AllTags": pct(alltags), "UAS": pct(uas), "LAS": pct(las), "LAS_full": pct(las_full),
        "per_upos": {t: {"n": c, "acc": round(100 * per_ok[t] / c, 2)} for t, c in sorted(per_gold.items())},
        "top_confusions": [{"gold": g, "pred": p, "count": c} for (g, p), c in conf.most_common(10)]
    }

def format_report(r: dict) -> str:
    lines = [f"sentences={r['sentences']} words={r['words']} skipped={r['skipped_sentences']}",
             " ".join(f"{k}={r[k]:.2f}" for k in ("UPOS", "UFeats", "Lemma", "AllTags", "UAS", "LAS", "LAS_full")),
             "per-UPOS accuracy:"]
    lines += [f"  {t:6s} n={v['n']:5d}  acc={v['acc']:.1f}" for t, v in r["per_upos"].items()]
    if r["top_confusions"]:
        lines.append("top UPOS confusions (gold -> pred):")
        lines += [f"  {c['gold']} -> {c['pred']}: {c['count']}" for c in r["top_confusions"]]
    return "\n".join(lines)