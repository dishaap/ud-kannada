"""
Whitespace + punctuation tokeniser used ONLY to create the initial CoNLL-U skeleton

tokenize.py does not split Kannada clitics or sandhi; human annotator decides those
(docs/decisions.md). Returns (form, space_after) pairs
"""
from __future__ import annotations

from text import is_abbrev

OPEN = set("\"“‘'([{«")
CLOSE = set(".,;:!?\"”’')]}»…")

def tokenize(sentence: str) -> list[tuple[str, bool]]:
    """Return tokens as a list of tuples containing (form, space_after)."""
    chunks = sentence.split(" ")
    out: list[tuple[str, bool]] = []
    for ci, chunk in enumerate(chunks):
        if not chunk:
            continue
        last = ci == len(chunks) - 1
        lead: list[str] = []
        trail: list[str] = []
        core = chunk
        while core and core[0] in OPEN:
            lead.append(core[0])
            core = core[1:]
        while core and core[-1] in CLOSE:
            if core[-1] == "." and not trail and not last and is_abbrev(core[:-1]):
                break   # keep the period on initials such as ಕೆ.
            trail.append(core[-1])
            core = core[:-1]
        trail.reverse()
        merged: list[str] = []
        for t in trail: # "..." -> one token 
            if t == "." and merged and set(merged[-1]) == ("."):
                merged[-1] += "."
            else:
                merged.append(t)
        pieces = lead + ([core] if core else[]) + merged
        for pi, p in enumerate(pieces):
            # pieces inside one whitespace chunk touch each other -> SpaceAfter=No
            out.append((p, pi == len(pieces) - 1))
    return out