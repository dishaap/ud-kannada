import unicodedata
from conftest import S1, S3, S5, S_LATIN
from udkn.text import FilterConfig, check_sentences, normalize, split_sentences
from udkn.tokenize import tokenize

def test_normalize_is_nfc_and_strips_zero_width():
    decomposed = unicodedata.normalize("NFKD", "ಕೋ ಕೀ ಕೈ ಕೊ")
    assert decomposed != "ಕೋ ಕೀ ಕೈ ಕೊ"          # NFKD really does decompose Kannada vowel signs
    assert normalize(decomposed) == "ಕೋ ಕೀ ಕೈ ಕೊ"
    assert normalize("ಕ‍ನ್ನಡ   ಭಾಷೆ") == "ಕನ್ನಡ ಭಾಷೆ"

def test_split_keeps_initials_together():
    par = f"{S1} {S5}"
    assert split_sentences(par) == [S1, S5]

def test_split_question_and_quote():
    out = split_sentences("ಇದು ಏನು? ಅದು ನದಿ ಆಗಿದೆ. \"ಹೌದು\" ಎಂದರು.")
    assert out == ["ಇದು ಏನು?", "ಅದು ನದಿ ಆಗಿದೆ.", "\"ಹೌದು\" ಎಂದರು."]

def test_split_ad_abbreviation_not_a_boundary():
    s = "ಕ್ರಿ.ಶ. 1200 ರಲ್ಲಿ ಈ ದೇವಾಲಯವನ್ನು ನಿರ್ಮಿಸಲಾಯಿತು."
    assert split_sentences(s) == [s]

def test_filters():
    assert check_sentences(S1) is None
    assert check_sentences(S3) == "too_short"
    assert check_sentences(S_LATIN) == "foreign_letters"
    assert check_sentences(S1[:-1]) == "no_terminal"
    assert check_sentences("(" + S1) == "unbalanced"
    assert check_sentences(S_LATIN, FilterConfig(max_foreign_letters=20)) is None

def test_tokenize_punct_and_spaceafter():
    toks = tokenize("\"ಹೌದು,\" ಎಂದು ಡಾ. ಕೆ. ರಾವ್ ಹೇಳಿದರು...")
    forms = [t for t, _ in toks]
    assert forms == ['"', "ಹೌದು", ",", '"', "ಎಂದು", "ಡಾ.", "ಕೆ.", "ರಾವ್", "ಹೇಳಿದರು", "..."]
    assert toks[0] == ('"', False) and toks[1] == ("ಹೌದು", False) and toks[2] == (",", False)  # touch next piece
    assert toks[3] == ('"', True)