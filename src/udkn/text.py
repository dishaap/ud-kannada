"""
Kannada text normalisation, sentence splitting and sentence filters.

Design rules (see docs/decisions.md)
    * Text is NFC.
    * We never delete words from a sentence. A sentence is kept whole or dropped.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Zero-width chracters + soft hyphen. Stripped before NFC (D2 in docs/decisions.md)
_STRIP = dict.fromkeys(map(ord, "​‌‍⁠﻿­"), None)

ABBREVS = {"ಕ್ರಿ.ಶ", "ಕ್ರಿ.ಪೂ"}      # most common abbreviations
_QUOTE_OPEN = "\"“‘'(["
_QUOTE_CLOSE = ")]\"”’'"
_SENT_START = re.compile(r"^[\"“‘'(\[]?[ಀ-೿0-9]")
_CAND = re.compile(r"([.?!]+)([\"”’')\]]*)(?=\s|$)")
_TERMINAL = re.compile(r"[.?!][\"”’')\]]?$")
_MARKUP = re.compile(r"[|{}<>=*#_~^\\@&]|https?:|www\.|\.com\b")

def is_kn(ch: str) -> bool:
    """Check whether character is within Unicode range for Kannada."""
    return "ಀ" <= ch <= "೿"

def normalize(text: str) -> str:
    """Normalise text to NFC."""
    t = text.translate(_STRIP).replace(" ", " ").replace(" ", " ")
    t = unicodedata.normalize("NFC", t)
    return re.sub(r"\s+", " ", t).strip()

def is_abbrev(word: str) -> bool:
    """Initials / abbreviations like ಕೆ  ಎಂ.ಜಿ  ಡಾ  ಕ್ರಿ.ಶ (word given WITHOUT its final period)."""
    w = word.strip(_QUOTE_OPEN + _QUOTE_CLOSE)
    if w in ABBREVS:
        return True
    parts = [p for p in w.split(".") if p]
    return bool(parts) and all(len(p) <= 2 and all(is_kn(c) for c in p) for p in parts)

def split_sentences(paragraph: str) -> list[str]:
    """Split sentences in a paragraph and return as list of strings."""
    par = normalize(paragraph)
    out: list[str] = []
    start = 0
    for m in _CAND.finditer(par):
        end = m.end()
        before = par[start:m.start()]
        prev = before.split(" ")[-1] if before else ""
        nxt = par[end:].lstrip()
        if m.group(1) == "." and (is_abbrev(prev) or prev.isdigit()):
            continue
        if nxt and not _SENT_START.match(nxt):
            continue
        out.append(par[start:end].strip())
        start = end
    rest = par[start:].strip()
    if rest:
        out.append(rest)
    return out

def kannada_ratio(s: str) -> float:
    """Return ratio of Kannada characters to total number of characters in a given string."""
    letters = [c for c in s if unicodedata.category(c)[0] in "LM"]
    return sum(is_kn(c) for c in letters) / len(letters) if letters else 0.0


@dataclass
class FilterConfig:
    """Limits for max/min tokens in a sentence, foreign characters, digits and punctuation. Configure according to strictness."""
    min_tokens: int = 6
    max_tokens: int = 30
    max_foreign_letters: int = 0        # non-Kannada letters (Latin etc.); 0 = none allowed
    max_digit_tokens: int = 2
    max_punct_ratio: float = 0.25

def check_sentences(s: str, cfg: FilterConfig = FilterConfig()) -> str | None:
    """Check validity of sentences. Return None if the sentence is acceptable, else a short reason code."""
    toks = s.split()
    if len(toks) < cfg.min_tokens:
        return "too_short"
    if len(toks) > cfg.max_tokens:
        return "too_long"
    if _MARKUP.search(s):
        return "markup"
    if sum(1 for c in s if c.isalpha() and not is_kn(c)) > cfg.max_foreign_letters:
        return "foreign_letters"
    if sum(1 for t in toks if any(c.isdigit() for c in t)) > cfg.max_digit_tokens:
        return "digits"
    if sum(1 for t in toks if not any(c.isalnum() for c in t)) / len(toks) > cfg.max_punct_ratio:
        return "punct"
    if not _SENT_START.match(s):
        return "bad_start"
    if not _TERMINAL.search(s):
        return "no_terminal"
    if s.count("(") != s.count(")") or s.count("[") != s.count("]") \
            or s.count("“") != s.count("”") or s.count('"') % 2:
        return "unbalanced"
    return None