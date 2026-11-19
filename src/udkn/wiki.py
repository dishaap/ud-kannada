"""
Kannada Wikipedia dump -> clean paragraphs.

Wikipedia text is CC BY-SA 4.0. Every sentence we keep carries its article id and
revision id (see pool.py) so attribution can be written into the treebank metadata.
"""
from __future__ import annotations

import bz2
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import mwparserfromhell

DUMP_URL = "https://dumps.wikimedia.org/knwiki/latest/knwiki-latest-pages-articles.xml.bz2"
# link namespaces whose captions must not leak into prose (English + Kannada names)
_SKIP_NS = {"file", "image", "category", "ಚಿತ್ರ", "ವರ್ಗ", "ಚಿತ್ರ", "ಕಡತ", "media"}
_BAD_LINE_START = ("=", "*", "#", ":", ";", "|", "!", "{", "<", "-")

@dataclass
class Page:
    page_id: int
    title: str
    rev_id: int
    text: str


def download(dest: str | Path, url: str = DUMP_URL) -> Path:
    """Download Wiki dump page to destination file."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} -> {dest}")
    urllib.request.urlretrieve(url, dest)
    return dest

def _local(tag: str) -> str:
    """Return name of tag of an element in XML file."""
    return tag.rsplit("}", 1)[-1]

def iter_pages(path: str | Path) -> Iterator[Page]:
    """Stream main-namespace, non-redirect pages from a MediaWiki XML export (.xml or .xml.bz2)."""
    opener = bz2.open if str(path).endswith(".bz2") else open
    with opener(path, "rb") as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            if _local(elem.tag) != "page":
                continue
            title = pid = rev = ns = text = None
            redirect = False
            for ch in elem:
                t = _local(ch.tag)
                if t == "title":
                    title = ch.text
                elif t == "ns":
                    ns = ch.text
                elif t == "id":
                    pid = ch.text
                elif t == "redirect":
                    redirect = True
                elif t == "revision":
                    for r in ch:
                        if _local(r.tag) == "id":
                            rev = r.text
                        elif _local(r.tag) == "text":
                            text = r.text
            elem.clear()
            if ns == "0" and not redirect and text and pid and title:
                yield Page(int(pid), title, int(rev or 0), text)


def clean_wikitext(raw: str) -> list[str]:
    """Wikitext -> list of prose lines (one per paragraph). Lists, tables, headings, templates are dropped."""
    t = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    t = re.sub(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", "", t, flags=re.S | re.I)
    t = re.sub(r"\{\|.*?\|\}", "", t, flags=re.S)
    code = mwparserfromhell.parse(t)
    for tpl in code.filter_templates(recursive=False):
        try:
            code.remove(tpl)
        except ValueError:
            pass
    for link in code.filter_wikilinks():
        title = str(link.title).strip().lower()
        if ":" in title and title.split(":", 1)[0].strip() in _SKIP_NS:
            try:
                code.remove(link)
            except ValueError:
                pass
    # strip_code() removes list/heading markers but KEEPS their text, so drop such lines first
    kept = [ln for ln in str(code).split("\n") if not ln.lstrip().startswith(_BAD_LINE_START)]
    plain = mwparserfromhell.parse("\n".join(kept)).strip_code(normalize=True, collapse=True)
    lines = []
    for ln in plain.split("\n"):
        ln = ln.strip()
        if len(ln) < 30 or ln.startswith(_BAD_LINE_START):
            continue
        lines.append(ln)
    return lines