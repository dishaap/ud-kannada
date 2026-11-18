# Decisions log

Record every annotation or pipeline decision here the day you make it, with 1–2 example sentences.
Reviewers and the second annotator will rely on this.

## Pipeline (made in code)
- D1 Source: Kannada Wikipedia (CC BY-SA 4.0), per-sentence article+revision kept. *Add other sources later for genre diversity.*
- D2 Text is NFC; zero-width chars (U+200B/C/D, U+2060, U+FEFF, soft hyphen) are stripped. *Revisit if ZWJ/ZWNJ matter for any word.*
- D3 Sentences of 6–30 whitespace tokens ending in . ? !; no sentence is edited, only kept or rejected.
- D4 Sentences with non-Kannada letters (Latin etc.) are dropped by default (`--max-foreign-letters`).
- D5 Splits are by article (10% test / 10% dev / 80% train by hash).

## To decide before annotating (fill in; check how Tamil/Telugu/Hindi UD treebanks do it)
- Tokenisation: emphatic/clitic `-ಉ -ಊ -ಏ -ಓ`, `-ಆ` (question), quotative `ಎಂದು`, `ಅಂತ`; sandhi; compound verbs; numerals + suffixes (`1200ರಲ್ಲಿ`); abbreviations/initials.
- Multiword tokens: split suffix postpositions/case (ಮನೆಗೆ = ಮನೆ+ಗೆ)? Default expectation: keep one word, mark case in FEATS.
- Copula: `ಇದೆ / ಆಗಿದೆ / ಅಲ್ಲ / ಇಲ್ಲ` (existential vs copula vs negative); `ಆಗು` as light/auxiliary.
- Verb forms: conjunctive participle (-ಿ/-ಇ), relative participles (-ದ/-ವ), infinitive (-ಲು/-ಅ), conditional; VERB vs AUX; light verbs (`ಮಾಡು`, `ಬರು`, `ಹಾಕು`).
- Case inventory in FEATS (Nom, Acc, Dat, Gen, Loc, Abl, Ins, Voc) and how postpositions map to `case`.
- Lemma convention: verb root (ಹೋಗು) vs infinitive; noun nominative singular.
- Person/gender/number on verbs (Kannada marks gender in 3rd person): which FEATS to include.
- Enhanced dependencies: out of scope for v1 (decision).
