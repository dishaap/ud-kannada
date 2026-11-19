"""
Build a sentence pool from Wikipedia, sample annotation batches, export CoNLL-U skeletons.

Splits are by DOCUMENT (article), never by sentence, to ensure neighbouring sentences don't leak 
between train/dev/test
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from . import conllu
from .text import FilterConfig, check_sentences, normalize, split_sentences
from .tokenize import tokenize
from .wiki import Page, clean_wikitext, iter_pages

def doc_split(page_id: int, seed: int = 0, dev: float = 0.1, test: float = 0.1) -> str:
    """Create a document split from available pool."""
    h = int(hashlib.sha1(f"{seed}:{page_id}".encode()).hexdigest(), 16) % 10_000 / 10_000
    return "test" if h < test else "dev" if h < test + dev else "train"

def source_url(page_id: int, rev_id: int) -> str:
    """Return URL string for requested page"""
    return f"https://kn.wikipedia.org/w/index.php?curid={page_id}&oldid={rev_id}"

def build_pool(dump: str | Path, out: str | Path, cfg: FilterConfig = FilterConfig(),
               seed: int = 0, limit_pages: int | None = None) -> dict:
    """Build pool from valid sentences and write to JSONL file."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    reasons: Counter = Counter()
    kept = pages = 0
    with out.open("w", encoding="utf-8") as fh:
        for page in iter_pages(dump):
            pages += 1
            if limit_pages and pages > limit_pages:
                break
            idx = 0
            for par in clean_wikitext(page.text):
                for sent in split_sentences(par):
                    sent = normalize(sent)
                    reasons["total"] += 1
                    why = check_sentences(sent, cfg)
                    if why:
                        reasons[why] += 1
                        continue
                    if sent in seen:
                        reasons["duplicate"] += 1
                        continue
                    seen.add(sent)
                    rec = {"id": f"knwiki-{page.page_id}-{idx}", "page_id": page.page_id,
                           "title": page.title, "rev_id": page.rev_id, "idx": idx,
                           "n_tokens": len(sent.split()), "split": doc_split(page.page_id, seed),
                           "text": sent}
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    idx += 1
                    kept += 1
    stats = {"pages": pages, "kept": kept, "rejected": dict(reasons), "filter": cfg.__dict__}
    Path(str(out) + ".stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats

def load_jsonl(path: str | Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]

def used_ids(*paths: str | Path) -> set[str]:
    """Sentence ids already sampled/annotated (from .jsonl pools or .conllu files)."""
    ids: set[str] = set()
    for p in paths:
        p = Path(p)
        if p.suffix == ".conllu":
            ids |= {s.sent_id for s in conllu.read(p) if s.sent_id}
        else:
            ids |= {r["id"] for r in load_jsonl(p)}
    return ids

def sample(pool: str | Path, n: int, split: str = "train", per_article_max: int = 3,
           seed: int = 0, exclude: set[str] | None = None) -> list[dict]:
    """Diverse sample: round-robin over shuffled articles, at most per_article_max each."""
    rng = random.Random(seed)
    exclude = exclude or set()
    by_page: dict[int, list[dict]] = defaultdict(list)
    for r in load_jsonl(pool):
        if r["split"] == split and r["id"] not in exclude:
            by_page[r["page_id"]].append(r)
    pages = sorted(by_page)
    rng.shuffle(pages)
    for p in pages:
        rng.shuffle(by_page[p])
    chosen: list[dict] = []
    for rnd in range(per_article_max):
        for p in pages:
            if len(chosen) >= n:
                break
            if len(by_page[p]) > rnd:
                chosen.append(by_page[p][rnd])
    chosen.sort(key=lambda r: (r["page_id"], r["idx"]))     # document order for annotation context
    return chosen

def to_sentences(records: list[dict]) -> list[conllu.Sentence]:
    """Convert records to sentences (comments + tokens)."""
    out = []
    last_page = None
    for r in records:
        comments = []
        if r["page_id"] != last_page:
            comments.append(f"# newdoc id = knwiki-{r['page_id']}")
            last_page = r["page_id"]
        comments += [f"# sent_id = {r['id']}", f"# text = {r['text']}",
                     f"# source = {source_url(r['page_id'], r['rev_id'])}",
                     f"# source_title = {r['title']}"]
        toks = []
        for i, (form, space_after) in enumerate(tokenize(r["text"]), 1):
            toks.append(conllu.Token(str(i), form, misc="_" if space_after else "SpaceAfter=No"))
        out.append(conllu.Sentence(comments, toks))
    return out
