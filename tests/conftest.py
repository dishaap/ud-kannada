import bz2
import pytest

S1 = "ಬೆಂಗಳೂರು ಕರ್ನಾಟಕದ ರಾಜಧಾನಿಯಾಗಿದ್ದು ದೇಶದ ಪ್ರಮುಖ ಮಹಾನಗರಗಳಲ್ಲಿ ಒಂದಾಗಿದೆ."
S2 = "ಕುವೆಂಪು ಅವರು ಕನ್ನಡದ ಪ್ರಸಿದ್ಧ ಕವಿ ಮತ್ತು ಕಾದಂಬರಿಕಾರರಾಗಿದ್ದರು."
S3 = "ಹಂಪಿಯು ವಿಜಯನಗರ ಸಾಮ್ರಾಜ್ಯದ ರಾಜಧಾನಿಯಾಗಿತ್ತು."  # only 5 apparent tokens -> too_short
S4 = "ಈ ನದಿಯು ಪಶ್ಚಿಮ ಘಟ್ಟಗಳಲ್ಲಿ ಹುಟ್ಟಿ ಪೂರ್ವಕ್ಕೆ ಹರಿದು ಬಂಗಾಳ ಕೊಲ್ಲಿಯನ್ನು ಸೇರುತ್ತದೆ."
S5 = "ಡಾ. ಕೆ. ಶಿವರಾಮ ಕಾರಂತರು ಕನ್ನಡದ ಪ್ರಮುಖ ಸಾಹಿತಿಯಾಗಿದ್ದರು."  # abbreviation
S_LATIN = "ಈ ನಗರವು ಇಂಗ್ಲಿಷ್ ನಲ್ಲಿ Bangalore ಎಂದು ಕರೆಯಲ್ಪಡುತ್ತದೆ ಎಂದು ಹೇಳಲಾಗುತ್ತದೆ."  # latin letters

WIKITEXT_1 = (
    "{{infobox city|name=x}}\n"
    f"'''ಬೆಂಗಳೂರು''' ಕರ್ನಾಟಕದ [[ರಾಜಧಾನಿ|ರಾಜಧಾನಿಯಾಗಿದ್ದು]] <ref>citation text here</ref>"
    " [[ದೇಶ|ದೇಶದ]] ಪ್ರಮುಖ ಮಹಾನಗರಗಳಲ್ಲಿ ಒಂದಾಗಿದೆ. " + S5 + "\n"
    "[[ಚಿತ್ರ:Vidhana.jpg|thumb|ವಿಧಾನ ಸೌಧದ ಚಿತ್ರ ಇದು ಕೇವಲ ಶೀರ್ಷಿಕೆ ಮಾತ್ರ.]]\n"
    "== ಇತಿಹಾಸ ==\n"
    "* ಪಟ್ಟಿಯ ಅಂಶ ಇದು ಒಂದು ಉದ್ದವಾದ ಪಟ್ಟಿಯ ಸಾಲು ಆಗಿದೆ ಎಂದು ತಿಳಿಯಿರಿ.\n"
    + S4 + " " + S3 + " " + S_LATIN + "\n"
    "{| class=wikitable\n| ಕೋಷ್ಟಕ ಸಾಲು ಇದು ಒಂದು ಕೋಷ್ಟಕದ ಸಾಲು ಆಗಿದೆ ಎಂದು ತಿಳಿಯಿರಿ.\n|}\n"
)
WIKITEXT_2 = S2 + " " + S2 + "\n"  # duplicate sentence inside + across pages

def _page(pid, title, text, ns=0, redirect=False):
    red = '<redirect title="x"/>' if redirect else ""
    return (f"<page><title>{title}</title><ns>{ns}</ns><id>{pid}</id>{red}"
            f"<revision><id>{pid * 10}</id><text>{text}</text></revision></page>")

@pytest.fixture
def dump(tmp_path):
    from xml.sax.saxutils import escape
    xml = ('<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/">'
           + _page(1, "ಬೆಂಗಳೂರು", escape(WIKITEXT_1))
           + _page(2, "ಕುವೆಂಪು", escape(WIKITEXT_2))
           + _page(3, "Talk", escape(S1), ns=1)
           + _page(4, "Redir", escape("#REDIRECT x"), redirect=True)
           + "</mediawiki>")
    p = tmp_path / "dump.xml.bz2"
    p.write_bytes(bz2.compress(xml.encode("utf-8")))
    return p