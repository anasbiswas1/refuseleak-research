# Scale table with five responders (notebook 16)

## Table 10

Domain 1 held-out test with seven attackers: the two main responders, a larger open one and two proprietary ones.

| System | Qwen2.5-7B-Instruct: largest attacker advantage | Llama-3.1-8B-Instruct: largest attacker advantage | Qwen2.5-14B-Instruct (4-bit): largest attacker advantage | Claude Haiku 5.5: largest attacker advantage | Claude Sonnet 5.5: largest attacker advantage | Qwen2.5-7B-Instruct: resolved | Llama-3.1-8B-Instruct: resolved | Qwen2.5-14B-Instruct (4-bit): resolved | Claude Haiku 5.5: resolved | Claude Sonnet 5.5: resolved |
|---|---|---|---|---|---|---|---|---|---|---|
| B0 Privileged agent | 0.562 | 0.751 | 0.724 | 0.549 | 0.447 | 0.567 | 0.607 | 0.523 | 0.367 | n/a |
| B1 Privacy prompt | 0.551 | 0.473 | 0.676 | 0.243 | 0.213 | 0.513 | 0.513 | 0.567 | 0.410 | n/a |
| B2 Output redaction | 0.499 | 0.597 | 0.604 | 0.502 | n/a | 0.567 | 0.607 | 0.530 | 0.377 | n/a |
| B3 Triggered refusal | 0.237 | 0.210 | 0.225 | 0.190 | n/a | 0.467 | 0.453 | 0.393 | 0.243 | n/a |
| B5 Post-filter RAG | 0.113 | 0.114 | 0.118 | 0.093 | n/a | 0.587 | 0.613 | 0.537 | 0.347 | n/a |
| O2 Full-view clarifier | 0.193 | 0.222 | 0.224 | 0.193 | n/a | 0.983 | 0.983 | 0.983 | 0.983 | n/a |
| B4 Universal reply | 0.023 | 0.023 | 0.023 | 0.023 | n/a | 0.483 | 0.483 | 0.483 | 0.483 | n/a |
| B6 Typed collapse | 0.023 | 0.023 | 0.032 | 0.023 | n/a | 0.483 | 0.483 | 0.483 | 0.483 | n/a |
| O1 Permitted-view oracle | 0.023 | 0.023 | 0.023 | 0.026 | n/a | 1.000 | 1.000 | 1.000 | 1.000 | n/a |
| SameView (selected) | 0.023 | 0.023 | 0.024 | 0.027 | 0.027 | 0.977 | 0.987 | 0.983 | 0.987 | 0.987 |

Note. Qwen2.5-14B-Instruct runs with its official 4-bit weights; the Claude models are reached through their API. SameView's scorer uses the model's option log-probabilities where the responder gives them and the permitted-view evidence alone where it does not (the Claude models); the configuration (L2-RT-pre) is the one selected for the main models. n/a: not run for that responder.
