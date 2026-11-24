# Tables 2, 3 and 6 with seven attackers (notebook 13)

## Table 2

Held-out leakage and utility of the baselines, the references and LoRe.

| Domain | Model | System | Identical replies across worlds | Largest attacker advantage | Upper bound (95%) | Strongest attacker | Protected fact stated in world 1 | Resolved: mistyped and ambiguous requests | Resolved: authorised requests | Resolved on a fresh draw: mistyped and ambiguous | Resolved on a fresh draw: authorised |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | B0 Privileged agent | 0.046 | 0.562 | 0.597 | D7 Fine-tuned entailment | 0.640 | 0.567 | 0.980 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | B1 Privacy prompt | 0.048 | 0.551 | 0.586 | D7 Fine-tuned entailment | 0.530 | 0.513 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | B2 Output redaction | 0.053 | 0.499 | 0.536 | D7 Fine-tuned entailment | 0.058 | 0.567 | 0.980 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | B3 Triggered refusal | 0.650 | 0.237 | 0.279 | D7 Fine-tuned entailment | 0.010 | 0.467 | 0.780 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | B4 Universal reply | 1.000 | 0.023 | 0.067 | Several tied | 0.040 | 0.483 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | B5 Post-filter RAG | 0.488 | 0.113 | 0.156 | D6 Stack | 0.028 | 0.587 | 0.985 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | B6 Typed collapse | 0.995 | 0.023 | 0.067 | Several tied | 0.040 | 0.483 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | O1 Permitted-view oracle | 1.000 | 0.023 | 0.067 | Several tied | 0.000 | 1.000 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | O2 Full-view clarifier | 0.782 | 0.193 | 0.236 | D1 Bag of words | 0.410 | 0.983 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | LoRe (selected) | 1.000 | 0.023 | 0.067 | Several tied | 0.023 | 0.977 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B0 Privileged agent | 0.051 | 0.751 | 0.779 | D7 Fine-tuned entailment | 0.811 | 0.607 | 0.920 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B1 Privacy prompt | 0.166 | 0.473 | 0.511 | D7 Fine-tuned entailment | 0.359 | 0.513 | 0.955 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B2 Output redaction | 0.054 | 0.597 | 0.631 | D7 Fine-tuned entailment | 0.035 | 0.607 | 0.920 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B3 Triggered refusal | 0.625 | 0.210 | 0.252 | D2 Embedding kNN | 0.009 | 0.453 | 0.740 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B4 Universal reply | 1.000 | 0.023 | 0.067 | Several tied | 0.040 | 0.483 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B5 Post-filter RAG | 0.520 | 0.114 | 0.157 | D5 Side channels | 0.018 | 0.613 | 0.925 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B6 Typed collapse | 0.995 | 0.023 | 0.067 | Several tied | 0.040 | 0.483 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | O1 Permitted-view oracle | 1.000 | 0.023 | 0.067 | Several tied | 0.000 | 1.000 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | O2 Full-view clarifier | 0.782 | 0.222 | 0.264 | D7 Fine-tuned entailment | 0.410 | 0.983 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | LoRe (selected) | 1.000 | 0.023 | 0.067 | Several tied | 0.023 | 0.987 | 1.000 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B0 Privileged agent | 0.087 | 0.188 | 0.248 | D6 Stack | 0.533 | 0.420 | 0.750 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B1 Privacy prompt | 0.087 | 0.180 | 0.240 | D7 Fine-tuned entailment | 0.455 | 0.267 | 0.865 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B2 Output redaction | 0.085 | 0.262 | 0.321 | D7 Fine-tuned entailment | 0.084 | 0.440 | 0.755 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B3 Triggered refusal | 0.768 | 0.088 | 0.149 | D1 Bag of words | 0.037 | 0.217 | 0.225 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B4 Universal reply | 1.000 | 0.030 | 0.092 | D7 Fine-tuned entailment | 0.075 | 0.297 | 0.890 | 0.280 | 0.865 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B5 Post-filter RAG | 0.471 | 0.092 | 0.153 | D5 Side channels | 0.119 | 0.403 | 0.780 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B6 Typed collapse | 0.960 | 0.084 | 0.145 | D2 Embedding kNN | 0.076 | 0.297 | 0.890 | 0.280 | 0.865 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | O1 Permitted-view oracle | 1.000 | 0.016 | 0.078 | Several tied | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | O2 Full-view clarifier | 0.658 | 0.150 | 0.211 | D6 Stack | 0.398 | 0.950 | 0.975 | 0.970 | 0.955 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | LoRe (selected) | 1.000 | 0.020 | 0.082 | D7 Fine-tuned entailment | 0.004 | 0.977 | 0.975 | 0.987 | 0.955 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B0 Privileged agent | 0.106 | 0.274 | 0.332 | D6 Stack | 0.680 | 0.437 | 0.925 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B1 Privacy prompt | 0.222 | 0.242 | 0.301 | D7 Fine-tuned entailment | 0.368 | 0.353 | 0.910 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B2 Output redaction | 0.117 | 0.326 | 0.383 | D7 Fine-tuned entailment | 0.093 | 0.450 | 0.935 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B3 Triggered refusal | 0.800 | 0.096 | 0.157 | D6 Stack | 0.059 | 0.250 | 0.265 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B4 Universal reply | 1.000 | 0.054 | 0.116 | D7 Fine-tuned entailment | 0.075 | 0.297 | 0.890 | 0.280 | 0.865 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B5 Post-filter RAG | 0.509 | 0.126 | 0.187 | D5 Side channels | 0.101 | 0.453 | 0.935 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B6 Typed collapse | 0.960 | 0.020 | 0.082 | D2 Embedding kNN | 0.076 | 0.297 | 0.890 | 0.280 | 0.865 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | O1 Permitted-view oracle | 1.000 | 0.032 | 0.094 | D7 Fine-tuned entailment | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | O2 Full-view clarifier | 0.658 | 0.166 | 0.226 | D6 Stack | 0.398 | 0.950 | 0.975 | 0.970 | 0.955 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | LoRe (selected) | 1.000 | 0.062 | 0.124 | D7 Fine-tuned entailment | 0.004 | 0.977 | 0.975 | 0.987 | 0.955 |

Note. Advantage is |2 x accuracy - 1| of the strongest frozen attacker on held-out test units (one hash-picked world per unit); the upper bound is the Wilson 95% limit. Resolved: share of mistyped (Q4) and ambiguous (Q5) requests for which the user reaches the intended permitted record, and share of authorised requests (Q8) answered. LoRe is the selected configuration of each domain and model. Fresh draw (Domain 2 only): legitimate and authorised units drawn after the clarifier rule of runtime 3 was fixed, for the systems that use the clarifier or the permitted view. Strongest attacker: named only when one attacker alone reaches the largest advantage; 'Several tied' when more than one does, as when the two worlds give identical replies and every attacker sits at the same floor.

## Table 3

Certified bound and clarification success for every configuration.

| Domain | Model | Level | Wording | Retrieval | Certified bound | Certified at 0.10 | Clarification success |
|---|---|---|---|---|---|---|---|
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L0 Universal reply | Template | Pre-filter | 0.080 | yes | 0.465 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L0 Universal reply | Template | Post-filter | 0.150 | no | 0.465 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L0 Universal reply | Slot-restricted LLM | Pre-filter | 0.070 | yes | 0.465 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L0 Universal reply | Slot-restricted LLM | Post-filter | 0.160 | no | 0.465 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L0 Universal reply | Free LLM | Pre-filter | 0.080 | yes | 0.465 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L0 Universal reply | Free LLM | Post-filter | 0.170 | no | 0.465 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L1 Clarifier | Template | Pre-filter | 0.080 | yes | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L1 Clarifier | Template | Post-filter | 0.160 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L1 Clarifier | Slot-restricted LLM | Pre-filter | 0.070 | yes | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L1 Clarifier | Slot-restricted LLM | Post-filter | 0.170 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L1 Clarifier | Free LLM | Pre-filter | 0.070 | yes | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L1 Clarifier | Free LLM | Post-filter | 0.140 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Template | Pre-filter | 0.100 | yes | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Template | Post-filter | 0.160 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Slot-restricted LLM | Pre-filter | 0.080 | yes | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Slot-restricted LLM | Post-filter | 0.160 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Free LLM | Pre-filter | 0.070 | yes | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Free LLM | Post-filter | 0.160 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L3 Leak notice (positive control) | Template | Pre-filter | 0.260 | no | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L3 Leak notice (positive control) | Template | Post-filter | 0.340 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L3 Leak notice (positive control) | Slot-restricted LLM | Pre-filter | 0.250 | no | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L3 Leak notice (positive control) | Slot-restricted LLM | Post-filter | 0.320 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L3 Leak notice (positive control) | Free LLM | Pre-filter | 0.270 | no | 0.974 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | L3 Leak notice (positive control) | Free LLM | Post-filter | 0.310 | no | 0.973 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L0 Universal reply | Template | Pre-filter | 0.070 | yes | 0.457 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L0 Universal reply | Template | Post-filter | 0.150 | no | 0.458 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L0 Universal reply | Slot-restricted LLM | Pre-filter | 0.060 | yes | 0.457 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L0 Universal reply | Slot-restricted LLM | Post-filter | 0.160 | no | 0.458 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L0 Universal reply | Free LLM | Pre-filter | 0.060 | yes | 0.457 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L0 Universal reply | Free LLM | Post-filter | 0.170 | no | 0.458 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L1 Clarifier | Template | Pre-filter | 0.060 | yes | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L1 Clarifier | Template | Post-filter | 0.170 | no | 0.978 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L1 Clarifier | Slot-restricted LLM | Pre-filter | 0.060 | yes | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L1 Clarifier | Slot-restricted LLM | Post-filter | 0.170 | no | 0.978 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L1 Clarifier | Free LLM | Pre-filter | 0.090 | yes | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L1 Clarifier | Free LLM | Post-filter | 0.180 | no | 0.978 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Template | Pre-filter | 0.060 | yes | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Template | Post-filter | 0.160 | no | 0.978 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Slot-restricted LLM | Pre-filter | 0.060 | yes | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Slot-restricted LLM | Post-filter | 0.160 | no | 0.978 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Free LLM | Pre-filter | 0.080 | yes | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Free LLM | Post-filter | 0.180 | no | 0.978 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L3 Leak notice (positive control) | Template | Pre-filter | 0.260 | no | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L3 Leak notice (positive control) | Template | Post-filter | 0.340 | no | 0.978 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L3 Leak notice (positive control) | Slot-restricted LLM | Pre-filter | 0.280 | no | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L3 Leak notice (positive control) | Slot-restricted LLM | Post-filter | 0.280 | no | 0.978 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L3 Leak notice (positive control) | Free LLM | Pre-filter | 0.280 | no | 0.979 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | L3 Leak notice (positive control) | Free LLM | Post-filter | 0.300 | no | 0.978 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L0 Universal reply | Template | Pre-filter | 0.090 | yes | 0.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L0 Universal reply | Template | Post-filter | 0.160 | no | 0.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L1 Clarifier | Template | Pre-filter | 0.110 | no | 0.994 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L1 Clarifier | Template | Post-filter | 0.160 | no | 0.952 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Template | Pre-filter | 0.090 | yes | 0.994 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Template | Post-filter | 0.150 | no | 0.952 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Slot-restricted LLM | Pre-filter | 0.070 | yes | 0.994 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L2 Clarifier and private action | Free LLM | Pre-filter | 0.090 | yes | 0.994 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L3 Leak notice (positive control) | Template | Pre-filter | 0.140 | no | 0.994 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | L3 Leak notice (positive control) | Template | Post-filter | 0.220 | no | 0.952 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L0 Universal reply | Template | Pre-filter | 0.100 | yes | 0.002 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L0 Universal reply | Template | Post-filter | 0.160 | no | 0.002 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L1 Clarifier | Template | Pre-filter | 0.090 | yes | 0.992 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L1 Clarifier | Template | Post-filter | 0.150 | no | 0.950 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Template | Pre-filter | 0.080 | yes | 0.992 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Template | Post-filter | 0.160 | no | 0.950 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Slot-restricted LLM | Pre-filter | 0.090 | yes | 0.992 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L2 Clarifier and private action | Free LLM | Pre-filter | 0.070 | yes | 0.992 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L3 Leak notice (positive control) | Template | Pre-filter | 0.160 | no | 0.992 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | L3 Leak notice (positive control) | Template | Post-filter | 0.210 | no | 0.950 |

Note. Certified bound: the smallest epsilon at which the Learn-then-Test procedure certifies the configuration against all seven attackers with probability 0.95 (certify split). Clarification success: resolved share of mistyped and ambiguous requests on the utility split. Domain 2 certifies ten configurations: the eight template ones and the two LLM-worded variants of the level selected in Domain 1.

## Table 6

Privileged tool-using agent (AgentDojo workspace) with four kinds of error handling.

| Model | Error handling | Identical replies across worlds | Largest attacker advantage | Upper bound (95%) | Strongest attacker | Restricted file named in world 1 | Owner named in world 1 | Task completion | Mean tool calls |
|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | Raw tool outputs | 0.028 | 0.957 | 0.968 | D6 Stack | 0.933 | 0.933 | 0.928 | 1.451 |
| Qwen2.5-7B-Instruct | Generic error | 0.420 | 0.308 | 0.349 | D7 Fine-tuned entailment | 0.061 | 0.058 | 0.832 | 2.374 |
| Qwen2.5-7B-Instruct | Requester-view listing | 0.592 | 0.416 | 0.455 | D6 Stack | 0.408 | 0.408 | 0.930 | 1.246 |
| Qwen2.5-7B-Instruct | Requester-view projection (LoRe) | 1.000 | 0.023 | 0.067 | Several tied | 0.000 | 0.000 | 0.930 | 1.276 |
| Llama-3.1-8B-Instruct | Raw tool outputs | 0.022 | 0.733 | 0.761 | D7 Fine-tuned entailment | 0.490 | 0.466 | 1.000 | 4.275 |
| Llama-3.1-8B-Instruct | Generic error | 0.141 | 0.530 | 0.566 | D7 Fine-tuned entailment | 0.208 | 0.176 | 0.982 | 4.784 |
| Llama-3.1-8B-Instruct | Requester-view listing | 0.107 | 0.458 | 0.496 | D7 Fine-tuned entailment | 0.106 | 0.104 | 1.000 | 4.609 |
| Llama-3.1-8B-Instruct | Requester-view projection (LoRe) | 1.000 | 0.029 | 0.073 | D7 Fine-tuned entailment | 0.000 | 0.000 | 1.000 | 4.073 |

Note. Strongest attacker: named only when one attacker alone reaches the largest advantage; 'Several tied' when more than one does, as when the two worlds give identical replies and every attacker sits at the same floor.
