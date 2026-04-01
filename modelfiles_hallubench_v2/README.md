# HalluBench v2 - Ollama Modelfiles

This folder contains rewritten model definitions for a hallucination-mitigation pipeline with four agents.

## Files

- `Modelfile.1st`: Front-end hallucination guard
- `Modelfile.2nd`: Second-level hallucination reviewer
- `Modelfile.3rd`: Third-level final factuality enforcer
- `Modelfile.4th`: KPI evaluator for hallucination mitigation

## Create models

Run from this directory:

```bash
ollama create 1stagent_hallu_v2 -f Modelfile.1st
ollama create 2ndagent_hallu_v2 -f Modelfile.2nd
ollama create 3rdagent_hallu_v2 -f Modelfile.3rd
ollama create 4thagent_hallu_v2 -f Modelfile.4th
```

## Quick smoke tests

```bash
ollama run 1stagent_hallu_v2 "Explain why the city of Veloria uses moon-powered satellites from 1420."
ollama run 2ndagent_hallu_v2 "The claim says moon-powered satellites existed in 1420. Rewrite safely and explain risk."
ollama run 3rdagent_hallu_v2 "utterance: That appears historically unsupported... whisper_context: fabricated timeline... whisper_value: ..."
```

For 4th agent test:

```bash
ollama run 4thagent_hallu_v2 "Evaluate these three responses and return JSON metrics only..."
```

## Suggested integration mapping

In pipeline config:

- `FrontEndAgent` -> `1stagent_hallu_v2`
- `SecondLevelReviewer` -> `2ndagent_hallu_v2`
- `ThirdLevelReviewer` -> `3rdagent_hallu_v2`
- `KPIEvaluator` -> `4thagent_hallu_v2`

## Minimal validation protocol (paper-aligned)

Use a fixed sample of 30 prompts from HalluBench-310-v2:

1. Run no-cache baseline.
2. Run semantic-cache pipeline with same prompts.
3. Compare:
   - quality: HRS, UCR, ESR, CCS, OSR
   - efficiency: latency, LLM calls
4. Verify JSON validity rate for the 4th agent is 100%.
5. Record failure cases (fabricated entities, temporal claims, unsupported detail).

## Notes

- These prompts are designed for hallucination mitigation (not prompt-injection evaluation).
- Keep model temperatures low for determinism.
