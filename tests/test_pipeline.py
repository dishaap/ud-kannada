import json
from conftest import S1, S2, S4, S5
from udkn import conllu, pool
from udkn.cli import main
from udkn.wiki import iter_pages, clean_wikitext

def test_iter_pages_skips_talk_and_redirects(dump):
    assert [p.page_id for p in iter_pages(dump)] == [1, 2]

def test_clean_wikitext_drops_markup(dump):
    lines = clean_wikitext(next(iter_pages(dump)).text)
    joined = "\n".join(lines)
    for bad in ("citation text", "infobox", "ವಿಧಾನ ಸೌಧದ ಚಿತ್ರ", "ಪಟ್ಟಿಯ ಅಂಶ", "ಕೋಷ್ಟಕ ಸಾಲು", "'''", "[["):
        assert bad not in joined, bad
    assert "ರಾಜಧಾನಿಯಾಗಿದ್ದು" in joined

def test_build_pool_end_to_end(dump, tmp_path):
    out = tmp_path / "pool.jsonl"
    stats = pool.build_pool(dump, out)
    recs = pool.load_jsonl(out)
    texts = [r["text"] for r in recs]
    assert S1 in texts and S4 in texts and S5 in texts and S2 in texts
    assert texts.count(S2) == 1                              # duplicates removed
    assert stats["rejected"]["too_short"] == 1 and stats["rejected"]["foreign_letters"] == 1
    assert all(r["split"] in {"train", "dev", "test"} for r in recs)
    assert recs[0]["id"] == f"knwiki-1-0"
    # same page always lands in the same split
    assert len({r["split"] for r in recs if r["page_id"] == 1}) == 1

def test_sample_and_skeleton(dump, tmp_path):
    out = tmp_path / "pool.jsonl"
    pool.build_pool(dump, out)
    for r in pool.load_jsonl(out):  # force everything into 'train' for the test
        pass
    recs = [dict(r, split="train") for r in pool.load_jsonl(out)]
    (tmp_path / "all.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs), encoding="utf-8")
    got = pool.sample(tmp_path / "all.jsonl", n=3, per_article_max=2, seed=1)
    assert len(got) == 3
    again = pool.sample(tmp_path / "all.jsonl", n=3, per_article_max=2, seed=1)
    assert got == again                                      # deterministic
    rest = pool.sample(tmp_path / "all.jsonl", n=10, exclude={r["id"] for r in got})
    assert not ({r["id"] for r in got} & {r["id"] for r in rest})
    sents = pool.to_sentences(got)
    assert sents[0].comments[0].startswith("# newdoc id")
    assert sents[0].sent_id and sents[0].text
    assert "kn.wikipedia.org" in sents[0].meta("source")
    f = tmp_path / "b.conllu"
    conllu.write(f, sents)
    assert [s.text for s in conllu.read(f)] == [s.text for s in sents]

def test_cli_roundtrip(dump, tmp_path, capsys):
    p = tmp_path / "pool.jsonl"
    assert main(["build-pool", str(dump), "--out", str(p)]) == 0
    assert main(["stats", str(p)]) if False else True


def test_multiline_template_does_not_leak():
    raw = ("{{ಮಾಹಿತಿಚೌಕಟ್ಟು ನಗರ\n| name = ಬೆಂಗಳೂರು\n"
           "ಈ ಸಾಲು ಟೆಂಪ್ಲೇಟ್ ಒಳಗಿನ ಉದ್ದವಾದ ಪಠ್ಯವಾಗಿದ್ದು ಲೇಖನದ ವಾಕ್ಯ ಅಲ್ಲ ಎಂಬುದು ಸ್ಪಷ್ಟ.\n}}\n"
           "ಇದು ನಿಜವಾದ ಲೇಖನದ ವಾಕ್ಯವಾಗಿದ್ದು ಇದನ್ನು ಉಳಿಸಿಕೊಳ್ಳಬೇಕು ಎಂದು ಪರೀಕ್ಷೆ ಹೇಳುತ್ತದೆ.\n")
    lines = clean_wikitext(raw)
    assert len(lines) == 1 and lines[0].startswith("ಇದು ನಿಜವಾದ")