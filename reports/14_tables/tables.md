# Scale check (notebook 14)

## Table 10

Domain 1 held-out test with seven attackers: largest attacker advantage and share of mistyped and ambiguous requests resolved, for the two main responders and a larger one.

| System | Qwen2.5-7B-Instruct: largest attacker advantage | Llama-3.1-8B-Instruct: largest attacker advantage | Qwen2.5-14B-Instruct (4-bit): largest attacker advantage | Qwen2.5-7B-Instruct: resolved | Llama-3.1-8B-Instruct: resolved | Qwen2.5-14B-Instruct (4-bit): resolved |
|---|---|---|---|---|---|---|
| B0 Privileged agent | 0.562 | 0.751 | 0.724 | 0.567 | 0.607 | 0.523 |
| B1 Privacy prompt | 0.551 | 0.473 | 0.676 | 0.513 | 0.513 | 0.567 |
| B2 Output redaction | 0.499 | 0.597 | 0.604 | 0.567 | 0.607 | 0.530 |
| B3 Triggered refusal | 0.237 | 0.210 | 0.225 | 0.467 | 0.453 | 0.393 |
| B5 Post-filter RAG | 0.113 | 0.114 | 0.118 | 0.587 | 0.613 | 0.537 |
| O2 Full-view clarifier | 0.193 | 0.222 | 0.224 | 0.983 | 0.983 | 0.983 |
| B4 Universal reply | 0.023 | 0.023 | 0.023 | 0.483 | 0.483 | 0.483 |
| B6 Typed collapse | 0.023 | 0.023 | 0.032 | 0.483 | 0.483 | 0.483 |
| O1 Permitted-view oracle | 0.023 | 0.023 | 0.023 | 1.000 | 1.000 | 1.000 |
| LoRe (selected) | 0.023 | 0.023 | 0.024 | 0.977 | 0.987 | 0.983 |

Note. Qwen2.5-14B-Instruct runs with its official 4-bit weights. LoRe's scorer is refitted on each responder's own option scores; the configuration (L2-RT-pre) is the one selected for both main models.
