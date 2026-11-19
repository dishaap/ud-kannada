"""
Minimal, dependency free CoNLL-U reader/writer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

COLS = ["id", "form", "lemma", "upos", "xpos", "feats", "head", "deprel", "deps", "misc"]

@dataclass
class Token:
    id: str
    form: str
    lemma: str = "_"
    upos: str = "_"
    xpos: str = "_"
    feats: str = "_"
    head: str = "_"
    deprel: str = "_"
    deps: str = "_"
    misc: str = "_"

    @property
    def is_word(self) -> bool:
        return self.id.isdigit()    # excludes ranges (1-2) and empty nodes (1.1)

    def line(self) -> str:
        """Create one line entry from attributes"""
        return "\t".join(getattr(self, c) for c in COLS)

@dataclass
class Sentence:
    comments: list[str] = field(default_factory=list)
    tokens: list[Token] = field(default_factory=list)

    def meta(self, key: str) -> str | None:
        for c in self.comments:
            if c.startswith("# ") and "=" in c:
                k, v = c[2:].split("=", 1)
                if k.strip() == key:
                    return v.strip()
        return None

    @property
    def sent_id(self) -> str | None:
        return self.meta("sent_id")

    @property
    def text(self) -> str | None:
        return self.meta("text")

    @property
    def words(self) -> list[Token]:
        return [t for t in self.tokens if t.is_word]

def parse_feats(feats: str) -> dict[str, str]:
    """Parse features and return as dict"""
    return {} if feats == "_" else dict(kv.split("=", 1) for kv in feats.split("/"))

def parse(text: str) -> list[Sentence]:
    """Parse Token and comments and return as list of Sentence"""
    sents: list[Sentence] = []
    cur = Sentence()
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\n")
        if not line.strip():
            if cur.tokens or cur.comments:
                sents.append(cur)
            cur = Sentence()
        elif line.startswith("#"):
            cur.comments.append(line)
        else:
            cols = line.split("\t")
            if len(cols) != 10:
                raise ValueError(f"line {ln}: expected 10 tab-separated columns, go {len(cols)}")
            cur.tokens.append(Token(*cols))
    if cur.tokens or cur.comments:
        sents.append(cur)
    return sents

def read(path: str | Path) -> list[Sentence]:
    """Helper to fetch sentences from file and parse as list of Sentence"""
    return parse(Path(path).read_text(encoding="utf-8"))

def format_sentences(sents: Iterable[Sentence]) -> str:
    """Pretty formatting for comments + tokens blocks"""
    blocks = []
    for s in sents:
        blocks.append("\n".join(list(s.comments) + [t.line() for t in s.tokens]))
    return "\n\n".join(blocks) + "\n"

def write(path: str | Path, sents: Iterable[Sentence]) -> None:
    """Write list of Sentence to file with correct format."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(format_sentences(sents), encoding="utf-8")