# Hallucination mitigation with nested learning and semantic caching

Measurements, code and results for a three-stage multi-agent pipeline orchestrated over
the Open Floor Protocol, evaluated on 310 prompts with five KPIs, together with the human
annotation and the cross-family judge study reported in the paper.

- Paper: [arXiv:2605.29055](https://arxiv.org/abs/2605.29055)
- Earlier line of work: [arXiv:2501.13946](https://arxiv.org/abs/2501.13946)

---

## Prompt and response text is deliberately not released

This repository releases **measurements, not text**. The 310 prompts, the 930 stage
responses and the fabricated claims are withheld.

The reason is specific rather than precautionary. The 93 stress prompts ask the pipeline
to expand claims we invented, and several of those claims attribute actions to real
institutions — a WHO trial, an FDA approval, an IMF mandate, a CERN report. The point of
the study is that a fraction of the final responses assert those inventions as fact, in
fluent prose. Publishing that text on a scraped, indexed platform would put well-written
institutional misinformation into circulation, and no README travels with a scraped file.

What is released instead is everything needed to check the analysis: the per-prompt KPI
values at every stage, the cache-hit flags, the human labels, and the complete output of
all four judge configurations. See *What can and cannot be reproduced* below for exactly
where the line falls. The withheld text is available to researchers on request to the
authors.

---

## Repository layout

This repository holds two generations of material, kept side by side rather than overwritten.

| Path | Contents |
|---|---|
| `v2/` | Everything belonging to the current paper: the per-prompt measurements, the human annotation, the judge re-scoring, the figures under the corrected sign convention, and the code. This is what the paper refers to. |
| `v1/` | The earlier release, retained so that the first version of the paper remains checkable: the placeholder pipeline notebook, the Ollama `Modelfile` definitions, and the two aggregate summaries. Its figures and its aggregate THS values follow the superseded sign convention and should not be compared with `v2/`. |

The `v1/modelfiles_hallubench_v2/` directory carries a confusing name: the `v2` in it refers to the second revision of the Modelfiles, not to `v2/` in this repository. It is left as it was rather than renamed, because the paper's appendix refers to it under that name.

---

## What is here

### `v2/data/`

| File | Rows | Description |
|---|---|---|
| `kpi_per_prompt.csv` | 310 | One row per prompt: the five KPI values at each of the three stages, cache-hit flags, response length in words, a 12-character SHA-256 prefix of each response, the realistic/stress subset label, and a flag marking the 27 rows where the evaluator's output was substituted. |
| `judge_llama3_1_latest_930.csv` | 930 | Llama 3.1 8B re-scoring under the specified instrument |
| `judge_gemma4_12b_930.csv` | 930 | Gemma 4 12B, same instrument |
| `judge_qwen3_8b_930.csv` | 930 | Qwen 3 8B, same instrument |
| `judge_gemma4_12b_orig_930.csv` | 930 | Gemma 4 12B under the *original* instrument, the fourth cell of the factorial |
| `judge_gemma4_12b_orig_930_failures.log` | — | Raw output of every call that failed schema conformance in that run. It contains the judge's JSON only, and is the direct evidence for the five-key vocabulary discussed in the paper. |

The response hashes let anyone holding a copy of the text confirm they have the same
responses these measurements were taken from. Every judge row carries the model's weight
digest, the sampling seed and `num_ctx`.

### `v2/annotation/`

| File | Description |
|---|---|
| `CODEBOOK.md` | The annotation codebook, frozen before the data were inspected |
| `labels_coder_A.xlsx`, `_B`, `_C` | Each annotator's 93 labels, with the five-point scale, and no response text |
| `REF3_scored.csv` | The three label sets joined, with majority resolution and the corresponding ECS value |

Krippendorff's ordinal alpha across the three coders is 0.586, below the 0.667
conventionally treated as a floor, and we report it as such.

### `v2/code/`

`verify_paper_numbers.py` recomputes every number the paper reports from the files in this
repository and compares each one against the value printed in the paper, one line per check.
It runs on the released data alone, needs only pandas, and exits non-zero if any check fails,
so it doubles as a regression test on these artifacts. `judge_v2.py` is the specified
instrument: one response per call, stage identity withheld,
descriptive KPI definitions, JSON schema, fixed seed, pinned weight digest.
`judge_2x2.py` replays the original instrument against any model. Both take the full
per-prompt file as input and therefore cannot be run against the released data; they are
published so the measurement procedure can be read and criticised, and so that anyone with
their own pipeline outputs can apply the same instrument. `regen_figures.py` produces the
figures; see `v2/code/regen_figures_note.txt`.

### `v2/figures/`

Nine figures under the corrected sign convention of Equation 1. To confirm you have the
current set rather than an earlier one, check `nl_ths_comparison_all_scenarios.png`: the
SecurityFirst bar at the first stage is **above** zero.

---

## What can and cannot be reproduced from this repository

**Reproducible.** The per-stage KPI means. The exact per-KPI decomposition of the
aggregate, end to end and by step. The cache hit rate and its per-stage breakdown. The
identification of the 27 substituted rows, given here directly as a column. The human
annotation, its agreement statistics, and the alignment of each judge configuration with
the human labels. Every figure. Running `python v2/code/verify_paper_numbers.py` checks all of
these against the values printed in the paper in a single pass.

**Not reproducible without the text.** Re-running any judge over the responses, since the
instrument takes the originating request and the response as input. The realised cosine
similarities of the 444 cache hits, which are computable from the prompts and the served
responses but not from measurements alone. Any independent re-annotation.

---

## Known defects of the original run

Reported in the paper and repeated here because a reader working from these artifacts will
meet them.

**Substituted rows.** On 27 of the 310 prompts the KPI Evaluator returned a five-key
vocabulary from its own configuration instead of the four KPIs the harness requested, and
the harness wrote fixed values into the dataset. Those rows are flagged in
`kpi_per_prompt.csv`. Their substituted values trend monotonically across stages and
therefore encode an improvement by construction.

**The failure is not reproducible.** An earlier pass over the same prompts failed on 46
rows rather than 27, overlapping on two promptids against 4.0 expected under independence.
The evaluator was invoked through an interface that passes no sampling seed, so no pass is
re-executable; these measurements are one draw. The re-scoring in `data/judge_*.csv` uses a
fixed seed and constrained decoding, and produced no failure in 2,790 calls.

**Evaluator provenance.** The evaluator configuration in `v1/modelfiles_hallubench_v2/` was
authored after the final scoring pass and never compiled. The model that produced the KPI
values here carried a system prompt defining a different five-metric vocabulary,
reproduced verbatim in the paper's appendix.

**The memory tiers did not serve the cache hits.** The medium-term tier is consulted only
after a semantic miss and is keyed on an exact hash, so its measured hit count over the run
is zero; the long-term consolidation step has an empty body. All 444 hits came from the
semantic similarity cache, whose bound of 300 entries was never reached. The 47.7% figure
stands as measured.

**Sign convention.** The first version of the paper subtracted FGR while the evaluator was
instructed to score it as lower-is-better. The current version corrects this, and
everything here uses the corrected convention. Values differ from that version throughout.

**Two withdrawn figures.** Earlier versions of the paper reported, in Appendix A, a mean
first-stage ECS of 0.17 on the stress subset against 0.58 on the realistic subset. On this
dataset the two values are 0.450 and 0.432: the ordering was inverted, and the claim it
supported — that the fabrication prompts elicit a markedly less contextualized first-stage
response — does not hold. What the data show is that the two subsets separate downstream
rather than at entry, rising by 0.378 against 0.128. `verify_paper_numbers.py` checks the corrected values.

---

## Open work

The first-stage annotation, which would convert the 10.8% endorsement rate from a level
into a measured effect of the review stages, has not been performed. The realised cache-hit
similarities have not been computed.

## Security

No API keys, tokens or credentials are tracked. The pipeline calls a local Ollama over
HTTP. All judges are open-weight models run locally.

## Citation

Please cite the paper linked above and this repository.

## License

Code and Modelfiles are provided for research and educational use.
