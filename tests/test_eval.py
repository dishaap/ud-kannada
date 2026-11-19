import pytest
from udkn import conllu
from udkn.evaluate import TokenizationMismatch, evaluate
from udkn.iaa import agreement, cohen_kappa

GOLD = """# sent_id = a-1
# text = ಅವನು ಮನೆಗೆ ಹೋದನು .
1\tಅವನು\tಅವನು\tPRON\t_\tCase=Nom|Number=Sing\t3\tnsubj\t_\t_
2\tಮನೆಗೆ\tಮನೆ\tNOUN\t_\tCase=Dat\t3\tobl\t_\t_
3\tಹೋದನು\tಹೋಗು\tVERB\t_\tTense=Past\t0\troot\t_\t_
4\t.\t.\tPUNCT\t_\t_\t3\tpunct\t_\t_
"""

# prediction: wrong UPOS on tok2, wrong head on tok1, right head but wrong subtype on tok2
PRED = GOLD.replace("2\tಮನೆಗೆ\tಮನೆ\tNOUN", "2\tಮನೆಗೆ\tಮನೆ\tADV").replace(
    "3\tnsubj", "2\tnsubj").replace("3\tobl", "3\tobl:tmod")

def test_evaluate_perfect_and_imperfect():
    g = conllu.parse(GOLD)
    assert evaluate(g, conllu.parse(GOLD))["LAS"] == 100.0
    r = evaluate(g, conllu.parse(PRED))
    assert r["words"] == 4 and r["UPOS"] == 75.0 and r["UAS"] == 75.0
    assert r["LAS"] == 75.0           # obl:tmod counts as obl for LAS...
    assert r["LAS_full"] == 50.0      # ...but not for LAS_full
    assert r["top_confusions"][0] == {"gold": "NOUN", "pred": "ADV", "count": 1}

def test_tokenisation_mismatch():
    bad = GOLD.replace("ಮನೆಗೆ\tಮನೆ", "ಮನೆಗ\tಮನೆ")
    with pytest.raises(TokenizationMismatch):
        evaluate(conllu.parse(GOLD), conllu.parse(bad))
    assert evaluate(conllu.parse(GOLD), conllu.parse(bad), strict=False)["skipped_sentences"] == 1

def test_kappa_and_iaa():
    assert cohen_kappa(list("aabb"), list("aabb")) == 1.0
    assert cohen_kappa(list("aabb"), list("abab")) == 0.0
    s, rows = agreement(conllu.parse(GOLD), conllu.parse(PRED))
    assert s["UPOS_agree"] == 75.0 and any(r["field"] == "upos" for r in rows)