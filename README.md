# Hallucination mitigation with nested learning and semantic caching

Research code and materials for a multi-agent LLM pipeline that targets **hallucination risk** (HRS and related KPIs), **nested learning** with per-agent Continuum Memory Systems (MTM/LTM), and **semantic caching** (cosine similarity threshold τ = 0.87) to cut redundant inference.

Public repository: [github.com/diegogosmar/HalllucinationMitCaching](https://github.com/diegogosmar/HalllucinationMitCaching).

## What is included

| Item | Description |
|------|-------------|
| `NL_agentic_hallucination_300_embed_placeholder.ipynb` | Main experiment notebook. **Does not embed the 310 benchmark prompts.** Loads prompts from `hallubench_310_v2.csv` when present; otherwise uses deterministic placeholders. |
| `modelfiles_hallubench_v2/` | Ollama `Modelfile` definitions for the four roles (three pipeline agents + KPI evaluator role naming in docs). |
| `NL_Hallucination_Paper/` | LaTeX source (`agentic_hallu_NL_finals.tex`, `agentichallucinations.bib`) and assets needed to build the paper (ORCID icon, architecture diagrams). |
| `*.png` (repo root) | Example result figures (KPI comparison, THS-O evolution, cache utilization, scenario distributions) produced by the notebook. |
| `summary_statistics.csv`, `isr_distribution.csv` | **Aggregate** run summaries only (no per-prompt text). |

## What is excluded from this repository

To avoid publishing benchmark text and full model traces:

- The notebook **`NL_agentic_hallucination_300_embed.ipynb`** (prompts embedded in code) is **not** tracked.
- **`hallubench_310_v2.csv`** / **`hallubench_310_v2.jsonl`** are **not** tracked (full prompt corpus).
- **`pipeline_results*.csv`**, **`results_complete.csv`**, and **`pipeline.log`** are **not** tracked (they contain prompts and full responses).

If you have these files locally from a private copy of the project, place the CSV next to the placeholder notebook to reproduce the full benchmark.

## Security / secrets check

A scan of tracked sources shows **no API keys, tokens, or passwords**. The pipeline calls **Ollama locally** via the `ollama` CLI; the paper mentions using an external LLM-as-judge (e.g. Claude) in the evaluation setup—configure that only in your own environment if you replicate that part, and do not commit credentials.

## Requirements

- **Python** 3.10+ with packages in `requirements.txt`
- **Ollama** with base models matching your `Modelfile` `FROM` lines (e.g. Llama 2 / Llama 3.1 as configured)
- Models created from `modelfiles_hallubench_v2/` (see that folder’s README)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the notebook

1. Copy **`hallubench_310_v2.csv`** into this directory (same folder as the notebook) if you have it—columns must include **`prompt`** and **`style`** (217 × `realistic`, 93 × `stress`), 310 rows total.
2. Open **`NL_agentic_hallucination_300_embed_placeholder.ipynb`** and run all cells.
3. Without the CSV, the notebook runs with **placeholders only** (useful for structure checks; **not** comparable to published benchmark metrics).

## Building the paper

```bash
cd NL_Hallucination_Paper
pdflatex agentic_hallu_NL_finals.tex
bibtex agentic_hallu_NL_finals
pdflatex agentic_hallu_NL_finals.tex
pdflatex agentic_hallu_NL_finals.tex
```

Figures under `../` in the LaTeX file point to PNGs in the **repository root**; keep that layout when compiling.

## Related work

- Hallucination-focused agentic framework (prior line of work): [arXiv:2501.13946](https://arxiv.org/abs/2501.13946)
- Prompt-injection variant with nested learning and semantic caching: [arXiv:2601.13186](https://arxiv.org/abs/2601.13186)

## Citation

If you use this repository, please cite the associated paper(s) you rely on (see bibliography in `NL_Hallucination_Paper/agentichallucinations.bib`) and link to this repo.

## License

Unless otherwise noted in individual files, code and Modelfiles are provided for research and educational use. Benchmark text may be subject to separate terms if obtained from the authors.
