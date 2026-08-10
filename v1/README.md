# Hallucination mitigation with nested learning and semantic caching

Research code and materials for a multi-agent LLM pipeline that targets **hallucination mitigation** (KPIs including FCD/FGR/FDF/ECS/OSR where configured), **nested learning** with per-agent Continuum Memory Systems (MTM/LTM), and **semantic caching** (cosine similarity threshold τ = 0.87) to cut redundant inference.

## What is included

| Item | Description |
|------|-------------|
| `NL_agentic_hallucination_310_5kpi_placeholder.ipynb` | **Public** experiment notebook (definitive pipeline shape). Uses **310 synthetic placeholder prompts** — no HalluBench benchmark text in the repo. |
| `modelfiles_hallubench_v2/` | Ollama `Modelfile` definitions for the four roles (three pipeline agents + KPI evaluator role naming in docs). |
| `*.png` (repo root) | Example result figures (KPI comparison, THS evolution, cache utilization, scenario distributions) produced by the notebook. |
| `summary_statistics.csv`, `isr_distribution.csv` | **Aggregate** run summaries only (no per-prompt text). |

## What is excluded from this repository

To avoid publishing benchmark text and full model traces:

- The notebooks **`NL_agentic_hallucination_300_embed.ipynb`** and **`NL_agentic_hallucination_310_5kpi.ipynb`** (full benchmark prompts embedded in code) are **not** tracked.
- **`hallubench_310_v2.csv`** / **`hallubench_310_v2.jsonl`** are **not** tracked (full prompt corpus).
- **`pipeline_results*.csv`**, **`results_complete.csv`**, and **`pipeline.log`** are **not** tracked (they contain prompts and full responses).
- The **`NL_Hallucination_Paper/`** directory (LaTeX paper and its assets) is **not** tracked and is **not** part of the public repository.

If you have a private copy of **`NL_agentic_hallucination_310_5kpi.ipynb`** or the HalluBench CSV/JSONL, use them only locally — do not commit benchmark text or run logs that contain prompts and model outputs.

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

1. Install Python deps and Ollama models (see **Requirements** and `modelfiles_hallubench_v2/README.md`).
2. Open **`NL_agentic_hallucination_310_5kpi_placeholder.ipynb`** and run all cells (310 synthetic prompts; no benchmark corpus in the repo).
3. For **full HalluBench-310-v2 prompt text**, use a private checkout of **`NL_agentic_hallucination_310_5kpi.ipynb`** (gitignored) or obtain **`hallubench_310_v2.csv`** / **`hallubench_310_v2.jsonl`** separately and merge into your local copy as appropriate.

## Related work

- Hallucination-focused agentic framework (prior line of work): [arXiv:2501.13946](https://arxiv.org/abs/2501.13946)
- Prompt-injection variant with nested learning and semantic caching: [arXiv:2601.13186](https://arxiv.org/abs/2601.13186)

## Citation

If you use this repository, please cite the associated paper(s) you rely on (e.g. the arXiv entries under **Related work**) and link to this repo.

## License

Unless otherwise noted in individual files, code and Modelfiles are provided for research and educational use. Benchmark text may be subject to separate terms if obtained from the authors.
