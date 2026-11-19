from __future__ import annotations

import argparse
import json
import sys

from . import conllu, evaluate, iaa, pool, timelog, wiki
from .text import FilterConfig
from .validate import validate

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="udkn", description="Kannada UD treebank tooling")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("wiki-download", help="download the Kannada Wikipedia dump")
    s.add_argument("--dest", default="data/raw/knwiki-lates-pages-articles.xml.bz2")

    s = sub.add_parser("build-pool", help="dump -> filtered sentence pool (jsonl)")
    s.add_argument("dump"); s.add_argument("--out", default="data/pool/knwiki_pool.jsonl")
    s.add_argument("--seed", type=int, default=0); s.add_argument("--limit-pages", type=int)
    s.add_argument("--min_tokens", type=int, default=6); s.add_argument("--max-tokens", type=int, default=30)
    s.add_argument("--max-foreign-letters", type=int, default=0)

    s = sub.add_parser("sample", help="sample an annotation batch and write a CoNLL-U skeleton")
    s.add_argument("pool"); s.add_argument("--n", type=int, required=True)
    s.add_argument("--split", default="train", choices=["train", "dev", "test"])
    s.add_argument("--per-article-max", type=int, default=3)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--exclude", nargs="*", default=[], help=".jsonl/.conllu files whose sentence ids must be skipped")
    s.add_argument("--out", required=True, help="output .conllu (a .jsonl copy is written next to it)")

    s = sub.add_parser("eval", help="score predictions against gold")
    s.add_argument("gold"); s.add_argument("pred"); s.add_argument("--json"); s.add_argument("--lenient", action="store_true")

    s = sub.add_parser("iaa", help="inter-annotator agreement")
    s.add_argument("a"); s.add_argument("b"); s.add_argument("--disagreements", default="logs/disagreements.tsv")
    s.add_argument("--lenient", action="store_true")

    s = sub.add_parser("time", help="annotation time log")
    ts = s.add_subparsers(dest="tcmd", required=True)
    a = ts.add_parser("add")
    a.add_argument("--annotator", required=True); a.add_argument("--batch", required=True)
    a.add_argument("--phase", required=True, choices=timelog.PHASES)
    a.add_argument("--sentences", type=int, required=True); a.add_argument("--minutes", type=float, required=True)
    a.add_argument("--log", default="logs/time_log.csv")
    r = ts.add_parser("summary"); r.add_argument("--log", default="logs/time_log.csv")
    r.add_argument("--budget-hours", type=float, default=300)

    s = sub.add_parser("validate", help="run UD validator")
    s.add_argument("file"); s.add_argument("--level", type=int, default=2)

    s = sub.add_parser("stats", help="basic CoNLL-U statistics")
    s.add_argument("file")

    args = ap.parse_args(argv)

    if args.cmd == "wiki-download":
        wiki.download(args.dest)

    elif args.cmd == "build-pool":
        cfg = FilterConfig(args.min_tokens, args.max_tokens, args.max_foreign_letters)
        print(json.dumps(pool.build_pool(args.dump, args.out, cfg, args.seed, args.limit_pages),
                         ensure_ascii=False, indent=2))
        
    elif args.cmd == "sample":
        ex = pool.used_ids(*args.exclude) if args.exclude else set()
        recs = pool.sample(args.pool, args.n, args.split, args.per_article_max, args.seed, ex)
        conllu.write(args.out, pool.to_sentences(recs))
        with open(args.out.rsplit(".", 1)[0] + ".jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"wrote {len(recs)} sentences from {len({r['page_id'] for r in recs})} articles to {args.out}")
    
    elif args.cmd == "eval":
        rep = evaluate.evaluate(conllu.read(args.gold), conllu.read(args.pred), strict=not args.lenient)
        print(evaluate.format_report(rep))
        if args.json:
            open(args.json, "w", encoding="utf-8").write(json.dumps(rep, ensure_ascii=False, indent=2))
    
    elif args.cmd == "iaa":
        summ, rows = iaa.agreement(conllu.read(args.a), conllu.read(args.b), strict=not args.lenient)
        print(json.dumps(summ, indent=2))
        iaa.write_disagreements(rows, args.disagreements)
        print(f"{len(rows)} disagreements -> {args.disagreements}")

    elif args.cmd == "time":
        if args.tcmd == "add":
            timelog.add(args.log, args.annotator, args.batch, args.phase, args.sentences, args.minutes)
        print(timelog.summary(args.log, getattr(args, "budget_hours", 300)))

    elif args.cmd == "validate":
        return validate(args.file, args.level)

    elif args.cmd == "stats":
        sents = conllu.read(args.file)
        words = [w for s in sents for w in s.words]
        print(f"sentences={len(sents)}  words={len(words)} "
              f"avg_len={len(words) / max(len(sents), 1):.1f}")

    return 0

if __name__ == "__main__":
    sys.exit(main())