# Plan (Nov 2026 – Apr 2027, ~15 h/week ≈ 300 h)

| Phase | Weeks (Mon start) | Output |
|---|---|---|
| 0. Foundations | 1–2 (Nov 23, Nov 30) | Pool built and eyeballed; licence checked; read Tamil/Telugu/Hindi UD guidelines + Rama & Vajjala (Dravidian UD); decisions log started; contact UD early |
| 1. Gold seed | 3–5 (Dec 7 – Dec 21) | ~200 sentences annotated from scratch with NO model; 100 locked as gold test (document-level); second annotator recruited, ~10% double-annotated, first IAA |
| 2. Baselines | 5–7 (Dec 21 – Jan 4) | On the gold test set: projection (SimAlign) · zero-shot multilingual parser trained on Hindi/Telugu/Tamil · few-shot LLM pre-annotation. Pick the best pre-annotator |
| 3. Bootstrap loop | 7–18 (Jan 4 – Mar 15) | Batches of ~300: pre-annotate → correct → retrain. Log time per batch; adjudicate IAA disagreements |
| 4. Release | 18–21 (Mar 22 – Apr 12) | kn validator data, validator level 5 clean, README/metadata, licence, submit |

Hour budget (estimate, recalibrate after Phase 1): 40 h setup+guidelines · ~200 h annotation/correction ·
30 h second-annotator coordination + IAA · 30 h release. Use `udkn time summary` for the projection.
Expect 1,500–2,500 verified sentences. Everything released is human-verified.

Compute: no GPU needed locally. Training/pre-annotation runs on Colab (free T4 is enough for
fine-tuning a base-size multilingual encoder on a few thousand sentences); annotation needs only a laptop.
