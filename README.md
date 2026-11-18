# ud-kannada

Tooling and data pipeline for building a Universal Dependencies treebank for Kannada
(lemma, UPOS, FEATS, HEAD, DEPREL), human-verified, from Kannada Wikipedia text.

See `docs/plan.md` for the schedule and `docs/decisions.md` for annotation decisions.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
bash scripts/get_validator.sh                          # official UD validator -> vendor/ud-tools
pytest                                                 # 15 tests, no network needed
```

## Workflow
```bash
# 1. Get Kannada Wikipedia (~ a few hundred MB) and build a clean sentence pool
udkn wiki-download
udkn build-pool data/raw/knwiki-latest-pages-articles.xml.bz2 --out data/pool/knwiki_pool.jsonl
#    FIRST RUN: add --limit-pages 2000 and READ the pool by eye (see "Check the pool" below)

# 2. Sample a batch (document-level splits; <=3 sentences per article; never repeats earlier batches)
udkn sample data/pool/knwiki_pool.jsonl --n 200 --split test  --out data/batches/gold_test.conllu
udkn sample data/pool/knwiki_pool.jsonl --n 200 --split train --out data/batches/seed_001.conllu \
      --exclude data/batches/gold_test.jsonl

# 3. Annotate the .conllu in your editor (TODO: UD Annotatrix / Arborator-Grew / CoNLL-U Editor)

# 4. Measure
udkn time add --annotator me --batch seed_001 --phase scratch --sentences 25 --minutes 150
udkn time summary
udkn iaa annotatorA.conllu annotatorB.conllu          # kappa + a TSV of every disagreement
udkn eval gold.conllu predictions.conllu              # UPOS/UFeats/Lemma/UAS/LAS + per-tag table
udkn validate data/batches/seed_001.conllu --level 2  # raise the level as the treebank matures
```

## Check the pool (do this before anything else)
The extraction was tested only on a synthetic dump (this was built where Wikipedia was unreachable).
Run `build-pool --limit-pages 2000`, open `data/pool/knwiki_pool.jsonl.stats.json` to see why sentences
were rejected, and read ~100 random pool sentences. Look for: leftover markup, lists/tables leaking as
prose, wrong sentence boundaries, machine-looking text. Fix `wiki.py` / `text.py` before sampling.

## Licensing
Wikipedia text is **CC BY-SA 4.0**; the released treebank text must stay under a compatible licence and
keeps per-sentence `# source` (article + revision) metadata for attribution. [TODO: Confirm with UD's
contributing guidelines before release. Pick a licence for the code separately.]

## What is NOT here yet
Baselines/pre-annotation models (Colab notebooks), `kn` language data for the validator
(feature/deprel inventories), and the annotation guidelines — see the plan.
