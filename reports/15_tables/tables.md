# Tables (current form, notebook 15)

## Table 1

Overlap with existing work, disclosed before any method code (plan Section 2).

| Component | Status | Closest work | What is left for us |
|---|---|---|---|
| Phenomenon: refusals reveal protected facts | Taken | Agent Mosaic (2610.30418): refusal and disclosure labelled separately; refusals often state the composite. Benchmark only. | Clarification questions and tool-error strings, measured with a paired-world attacker, on open models |
| Collapse rule: same reply for hidden and absent | Taken as a rule | Stored Is Not Supported (He and Yu, 2609.02127): maps Withheld, Unknown, Unavailable to one view with fixed templates. Classical neither-confirm-nor-deny; OWASP generic login errors. | Their evaluation is 24 hand-written cases and they state it is not an end-to-end evaluation of language models. No LLM, no clarification, no utility study |
| Private controller, public responder | Taken | FIDES (2505.23643), CaMeL (2503.18813), KAIJU (2604.02375), APPA, SPA, Agent libOS | FIDES gives only explicit secrecy and leaves implicit flows through control flow open: this is exactly the refuse/ask/answer channel |
| Denial feedback through tools | Partly taken | Causality Laundering (2604.04035): provenance graph blocks later exfiltration; three scenarios, no distinguisher metric | User-visible distinguishability of errors; utility |
| Paired-world game | Partly taken | AgentSecBench (2605.26269): secret present vs absent; exact canary match; Qwen3 0.6B and 1.7B | Semantic attackers, refusals and clarifications as channels, 7B/8B models |
| Conformal ask-when-unsure | Taken in robotics | KnowNo (Ren et al., CoRL 2023, 2307.01928): conformal set over options, ask if more than one | Computing the set only over the requester's permitted view so asking is leak-free by construction |
| Cumulative leakage over a session | Partly taken | OCELOT (2606.12341): min-entropy budgets for PII releases; Multi-Stage Prompt Inference (2507.15613): binary-search extraction | Used as our adaptive attacker, not claimed |
| Statistical certificate of no leak for an LLM channel | Open | None found | Main contribution |
| Helping legitimate users under the certificate | Open | None found | Main contribution |

## Table 2

Held-out leakage and utility of the baselines, the references and SameView.

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
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | SameView (selected) | 1.000 | 0.023 | 0.067 | Several tied | 0.023 | 0.977 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B0 Privileged agent | 0.051 | 0.751 | 0.779 | D7 Fine-tuned entailment | 0.811 | 0.607 | 0.920 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B1 Privacy prompt | 0.166 | 0.473 | 0.511 | D7 Fine-tuned entailment | 0.359 | 0.513 | 0.955 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B2 Output redaction | 0.054 | 0.597 | 0.631 | D7 Fine-tuned entailment | 0.035 | 0.607 | 0.920 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B3 Triggered refusal | 0.625 | 0.210 | 0.252 | D2 Embedding kNN | 0.009 | 0.453 | 0.740 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B4 Universal reply | 1.000 | 0.023 | 0.067 | Several tied | 0.040 | 0.483 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B5 Post-filter RAG | 0.520 | 0.114 | 0.157 | D5 Side channels | 0.018 | 0.613 | 0.925 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | B6 Typed collapse | 0.995 | 0.023 | 0.067 | Several tied | 0.040 | 0.483 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | O1 Permitted-view oracle | 1.000 | 0.023 | 0.067 | Several tied | 0.000 | 1.000 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | O2 Full-view clarifier | 0.782 | 0.222 | 0.264 | D7 Fine-tuned entailment | 0.410 | 0.983 | 1.000 |  |  |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | SameView (selected) | 1.000 | 0.023 | 0.067 | Several tied | 0.023 | 0.987 | 1.000 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B0 Privileged agent | 0.087 | 0.188 | 0.248 | D6 Stack | 0.533 | 0.420 | 0.750 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B1 Privacy prompt | 0.087 | 0.180 | 0.240 | D7 Fine-tuned entailment | 0.455 | 0.267 | 0.865 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B2 Output redaction | 0.085 | 0.262 | 0.321 | D7 Fine-tuned entailment | 0.084 | 0.440 | 0.755 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B3 Triggered refusal | 0.768 | 0.088 | 0.149 | D1 Bag of words | 0.037 | 0.217 | 0.225 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B4 Universal reply | 1.000 | 0.030 | 0.092 | D7 Fine-tuned entailment | 0.075 | 0.297 | 0.890 | 0.280 | 0.865 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B5 Post-filter RAG | 0.471 | 0.092 | 0.153 | D5 Side channels | 0.119 | 0.403 | 0.780 |  |  |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | B6 Typed collapse | 0.960 | 0.084 | 0.145 | D2 Embedding kNN | 0.076 | 0.297 | 0.890 | 0.280 | 0.865 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | O1 Permitted-view oracle | 1.000 | 0.016 | 0.078 | Several tied | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | O2 Full-view clarifier | 0.658 | 0.150 | 0.211 | D6 Stack | 0.398 | 0.950 | 0.975 | 0.970 | 0.955 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | SameView (selected) | 1.000 | 0.020 | 0.082 | D7 Fine-tuned entailment | 0.004 | 0.977 | 0.975 | 0.987 | 0.955 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B0 Privileged agent | 0.106 | 0.274 | 0.332 | D6 Stack | 0.680 | 0.437 | 0.925 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B1 Privacy prompt | 0.222 | 0.242 | 0.301 | D7 Fine-tuned entailment | 0.368 | 0.353 | 0.910 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B2 Output redaction | 0.117 | 0.326 | 0.383 | D7 Fine-tuned entailment | 0.093 | 0.450 | 0.935 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B3 Triggered refusal | 0.800 | 0.096 | 0.157 | D6 Stack | 0.059 | 0.250 | 0.265 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B4 Universal reply | 1.000 | 0.054 | 0.116 | D7 Fine-tuned entailment | 0.075 | 0.297 | 0.890 | 0.280 | 0.865 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B5 Post-filter RAG | 0.509 | 0.126 | 0.187 | D5 Side channels | 0.101 | 0.453 | 0.935 |  |  |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | B6 Typed collapse | 0.960 | 0.020 | 0.082 | D2 Embedding kNN | 0.076 | 0.297 | 0.890 | 0.280 | 0.865 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | O1 Permitted-view oracle | 1.000 | 0.032 | 0.094 | D7 Fine-tuned entailment | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | O2 Full-view clarifier | 0.658 | 0.166 | 0.226 | D6 Stack | 0.398 | 0.950 | 0.975 | 0.970 | 0.955 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | SameView (selected) | 1.000 | 0.062 | 0.124 | D7 Fine-tuned entailment | 0.004 | 0.977 | 0.975 | 0.987 | 0.955 |

Note. Advantage is |2 x accuracy - 1| of the strongest frozen attacker on held-out test units (one hash-picked world per unit); the upper bound is the Wilson 95% limit. Resolved: share of mistyped (Q4) and ambiguous (Q5) requests for which the user reaches the intended permitted record, and share of authorised requests (Q8) answered. SameView is the selected configuration of each domain and model. Fresh draw (Domain 2 only): legitimate and authorised units drawn after the clarifier rule of runtime 3 was fixed, for the systems that use the clarifier or the permitted view. Strongest attacker: named only when one attacker alone reaches the largest advantage; 'Several tied' when more than one does, as when the two worlds give identical replies and every attacker sits at the same floor.

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

## Table 4

Ablations of SameView, replayed from the stored scores.

| Domain | Model | Variant | Component removed | Resolved | Wrong record given | Asked a question | Mean turns | Attribute questions asked | Access request filed when the record exists | Identical replies across worlds |
|---|---|---|---|---|---|---|---|---|---|---|
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | SameView as certified | none | 0.974 | 0.013 | 0.511 | 1.565 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | Score: permitted-view evidence only | candidate score | 0.987 | 0.000 | 0.524 | 1.532 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | Score: model log-probability only | candidate score | 0.984 | 0.002 | 0.949 | 2.009 | 12 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | No conformal set: answer the likeliest | conformal set | 0.638 | 0.331 | 0.000 | 1.000 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | No conformal set: always ask | conformal set | 0.987 | 0.000 | 0.989 | 1.990 | 1122 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | No attribute question: list the four likeliest | attribute question | 0.974 | 0.013 | 0.511 | 1.565 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | Always ask, no attribute question | attribute question (under always ask) | 0.987 | 0.000 | 0.989 | 1.991 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Qwen2.5-7B-Instruct | No private action (L1) | private access request | 0.974 | 0.013 | 0.511 | 1.565 | 0 | 0.000 | 1.000 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | SameView as certified | none | 0.979 | 0.008 | 0.524 | 1.573 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | Score: permitted-view evidence only | candidate score | 0.987 | 0.000 | 0.524 | 1.532 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | Score: model log-probability only | candidate score | 0.953 | 0.034 | 0.830 | 1.863 | 12 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | No conformal set: answer the likeliest | conformal set | 0.634 | 0.325 | 0.000 | 1.000 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | No conformal set: always ask | conformal set | 0.987 | 0.000 | 0.989 | 1.990 | 1122 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | No attribute question: list the four likeliest | attribute question | 0.979 | 0.008 | 0.524 | 1.573 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | Always ask, no attribute question | attribute question (under always ask) | 0.987 | 0.000 | 0.989 | 1.991 | 0 | 0.668 | 1.000 |
| Domain 1 (synthetic enterprise) | Llama-3.1-8B-Instruct | No private action (L1) | private access request | 0.979 | 0.008 | 0.524 | 1.573 | 0 | 0.000 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | SameView as certified | none | 0.994 | 0.000 | 1.000 | 2.106 | 38 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | Score: permitted-view evidence only | candidate score | 0.994 | 0.000 | 1.000 | 2.062 | 82 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | Score: model log-probability only | candidate score | 0.980 | 0.014 | 0.982 | 2.104 | 42 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | No conformal set: answer the likeliest | conformal set | 0.038 | 0.068 | 0.000 | 1.000 | 0 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | No conformal set: always ask | conformal set | 0.994 | 0.000 | 1.000 | 2.096 | 726 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | No attribute question: list the four likeliest | attribute question | 0.994 | 0.000 | 1.000 | 2.104 | 0 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | Always ask, no attribute question | attribute question (under always ask) | 0.994 | 0.000 | 1.000 | 2.014 | 0 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Qwen2.5-7B-Instruct | No private action (L1) | private access request | 0.994 | 0.000 | 1.000 | 2.106 | 38 | 0.000 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | SameView as certified | none | 0.992 | 0.002 | 0.996 | 2.116 | 60 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | Score: permitted-view evidence only | candidate score | 0.994 | 0.000 | 1.000 | 2.062 | 82 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | Score: model log-probability only | candidate score | 0.992 | 0.002 | 0.992 | 2.082 | 102 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | No conformal set: answer the likeliest | conformal set | 0.152 | 0.122 | 0.000 | 1.000 | 0 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | No conformal set: always ask | conformal set | 0.994 | 0.000 | 1.000 | 2.096 | 726 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | No attribute question: list the four likeliest | attribute question | 0.992 | 0.002 | 0.996 | 2.088 | 0 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | Always ask, no attribute question | attribute question (under always ask) | 0.994 | 0.000 | 1.000 | 2.016 | 0 | 0.765 | 1.000 |
| Domain 2 (Enron e-mail) | Llama-3.1-8B-Instruct | No private action (L1) | private access request | 0.992 | 0.002 | 0.996 | 2.116 | 60 | 0.000 | 1.000 |

Note. Each variant removes one component from the selected configuration and is replayed from the stored candidate scores. Access request filed when the record exists: share of existence requests in world 1 for which the private controller files a request with the record's owner (the reply is the same in both worlds).

## Table 5

Wording mode of the replies: template, slot-restricted and free LLM.

| Model | Wording | Temperature | Certified bound | Certified at 0.10 | Resolved: mistyped | Resolved: ambiguous | Same record codes as the template | Same number of options | Mean reply length (characters) | Identical replies across worlds |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | Template | none | 0.100 | yes | 0.974 | 0.974 | 1.000 | 1.000 | 264.038 | 1.000 |
| Qwen2.5-7B-Instruct | Slot-restricted LLM | 0 | 0.060 | yes | 0.974 | 0.974 | 1.000 | 1.000 | 236.758 | 1.000 |
| Qwen2.5-7B-Instruct | Free LLM | 0.7 | 0.070 | yes | 0.974 | 0.974 | 1.000 | 1.000 | 202.555 | 1.000 |
| Llama-3.1-8B-Instruct | Template | none | 0.060 | yes | 0.974 | 0.984 | 1.000 | 1.000 | 263.634 | 1.000 |
| Llama-3.1-8B-Instruct | Slot-restricted LLM | 0 | 0.060 | yes | 0.974 | 0.984 | 1.000 | 1.000 | 311.348 | 1.000 |
| Llama-3.1-8B-Instruct | Free LLM | 0.7 | 0.080 | yes | 0.974 | 0.984 | 1.000 | 1.000 | 483.870 | 1.000 |

## Table 6

Privileged tool-using agent (AgentDojo workspace) with four kinds of error handling.

| Model | Error handling | Identical replies across worlds | Largest attacker advantage | Upper bound (95%) | Strongest attacker | Restricted file named in world 1 | Owner named in world 1 | Task completion | Mean tool calls |
|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | Raw tool outputs | 0.028 | 0.957 | 0.968 | D6 Stack | 0.933 | 0.933 | 0.928 | 1.451 |
| Qwen2.5-7B-Instruct | Generic error | 0.420 | 0.308 | 0.349 | D7 Fine-tuned entailment | 0.061 | 0.058 | 0.832 | 2.374 |
| Qwen2.5-7B-Instruct | Requester-view listing | 0.592 | 0.416 | 0.455 | D6 Stack | 0.408 | 0.408 | 0.930 | 1.246 |
| Qwen2.5-7B-Instruct | Requester-view projection (SameView) | 1.000 | 0.023 | 0.067 | Several tied | 0.000 | 0.000 | 0.930 | 1.276 |
| Llama-3.1-8B-Instruct | Raw tool outputs | 0.022 | 0.733 | 0.761 | D7 Fine-tuned entailment | 0.490 | 0.466 | 1.000 | 4.275 |
| Llama-3.1-8B-Instruct | Generic error | 0.141 | 0.530 | 0.566 | D7 Fine-tuned entailment | 0.208 | 0.176 | 0.982 | 4.784 |
| Llama-3.1-8B-Instruct | Requester-view listing | 0.107 | 0.458 | 0.496 | D7 Fine-tuned entailment | 0.106 | 0.104 | 1.000 | 4.609 |
| Llama-3.1-8B-Instruct | Requester-view projection (SameView) | 1.000 | 0.029 | 0.073 | D7 Fine-tuned entailment | 0.000 | 0.000 | 1.000 | 4.073 |

## Table 7

Adaptive multi-turn attackers against SameView and the baselines.

| Model | Attacker | System | Test units | Identical transcripts across worlds | Advantage after one turn | Advantage after the last turn | Upper bound (95%) | Best learner | Protected fact stated in world 1 |
|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | A1 Attribute search | SameView (selected) | 2000 | 1.000 | 0.028 | 0.028 | 0.072 | Stack | 0.000 |
| Qwen2.5-7B-Instruct | A1 Attribute search | B1 Privacy prompt | 300 | 0.000 | 1.000 | 1.000 | 1.000 | Stack | 1.000 |
| Qwen2.5-7B-Instruct | A2 Five-query entailment | SameView (selected) | 6000 | 1.000 | 0.002 | 0.002 | 0.027 | Stack | 0.062 |
| Qwen2.5-7B-Instruct | A2 Five-query entailment | B1 Privacy prompt | 300 | 0.000 | 1.000 | 1.000 | 1.000 | Stack | 1.000 |
| Qwen2.5-7B-Instruct | A2 Five-query entailment | B3 Triggered refusal | 300 | 0.093 | 0.920 | 0.920 | 0.954 | Stack | 0.000 |
| Qwen2.5-7B-Instruct | A2 Five-query entailment | B5 Post-filter RAG | 600 | 0.212 | 0.157 | 0.343 | 0.416 | Side channels | 0.053 |
| Qwen2.5-7B-Instruct | A3 Count and list | SameView (selected) | 2000 | 1.000 | 0.017 | 0.017 | 0.061 | Stack | 0.040 |
| Qwen2.5-7B-Instruct | A3 Count and list | B3 Triggered refusal | 300 | 1.000 | 0.060 | 0.060 | 0.171 | Stack | 0.040 |
| Qwen2.5-7B-Instruct | A3 Count and list | B5 Post-filter RAG | 300 | 0.380 | 0.073 | 0.247 | 0.353 | Stack | 0.020 |
| Qwen2.5-7B-Instruct | A4 Misspelt names | SameView (selected) | 2000 | 1.000 | 0.017 | 0.017 | 0.061 | Stack | 0.002 |
| Qwen2.5-7B-Instruct | A4 Misspelt names | B3 Triggered refusal | 300 | 0.010 | 0.913 | 0.953 | 0.977 | Stack | 0.003 |
| Qwen2.5-7B-Instruct | A4 Misspelt names | B5 Post-filter RAG | 300 | 0.393 | 0.167 | 0.147 | 0.256 | Bag of words | 0.050 |
| Llama-3.1-8B-Instruct | A1 Attribute search | SameView (selected) | 2000 | 1.000 | 0.028 | 0.028 | 0.072 | Stack | 0.000 |
| Llama-3.1-8B-Instruct | A1 Attribute search | B1 Privacy prompt | 300 | 0.000 | 0.653 | 0.987 | 0.996 | Stack | 0.930 |
| Llama-3.1-8B-Instruct | A2 Five-query entailment | SameView (selected) | 6000 | 1.000 | 0.002 | 0.002 | 0.027 | Stack | 0.062 |
| Llama-3.1-8B-Instruct | A2 Five-query entailment | B1 Privacy prompt | 300 | 0.000 | 0.653 | 0.900 | 0.939 | Stack | 0.980 |
| Llama-3.1-8B-Instruct | A2 Five-query entailment | B3 Triggered refusal | 300 | 0.093 | 0.920 | 0.920 | 0.954 | Stack | 0.000 |
| Llama-3.1-8B-Instruct | A2 Five-query entailment | B5 Post-filter RAG | 600 | 0.212 | 0.113 | 0.330 | 0.403 | Side channels | 0.088 |
| Llama-3.1-8B-Instruct | A3 Count and list | SameView (selected) | 2000 | 1.000 | 0.017 | 0.017 | 0.061 | Stack | 0.040 |
| Llama-3.1-8B-Instruct | A3 Count and list | B3 Triggered refusal | 300 | 1.000 | 0.060 | 0.060 | 0.171 | Stack | 0.013 |
| Llama-3.1-8B-Instruct | A3 Count and list | B5 Post-filter RAG | 300 | 0.380 | 0.073 | 0.253 | 0.359 | Stack | 0.000 |
| Llama-3.1-8B-Instruct | A4 Misspelt names | SameView (selected) | 2000 | 1.000 | 0.017 | 0.017 | 0.061 | Stack | 0.002 |
| Llama-3.1-8B-Instruct | A4 Misspelt names | B3 Triggered refusal | 300 | 0.010 | 0.913 | 0.947 | 0.973 | Side channels | 0.003 |
| Llama-3.1-8B-Instruct | A4 Misspelt names | B5 Post-filter RAG | 300 | 0.393 | 0.153 | 0.180 | 0.288 | Side channels | 0.043 |

## Table 8

Side-channel attacker advantage per channel set.

| Units | Model | System | As built: advantage | As built: upper bound | Padding removed: advantage | Padding removed: upper bound | Length only: advantage | Length only: upper bound | Citations only: advantage | Citations only: upper bound | Options only: advantage | Options only: upper bound | Status code only: advantage | Status code only: upper bound | Latency only: advantage | Latency only: upper bound |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| held-out test | Qwen2.5-7B-Instruct | B0 Privileged agent | 0.132 | 0.175 | 0.084 | 0.127 | 0.099 | 0.142 | 0.084 | 0.127 | 0.023 | 0.067 | 0.023 | 0.067 | 0.096 | 0.139 |
| held-out test | Qwen2.5-7B-Instruct | B1 Privacy prompt | 0.213 | 0.255 | 0.241 | 0.283 | 0.162 | 0.205 | 0.179 | 0.222 | 0.023 | 0.067 | 0.023 | 0.067 | 0.145 | 0.188 |
| held-out test | Qwen2.5-7B-Instruct | B2 Output redaction | 0.212 | 0.254 | 0.212 | 0.254 | 0.138 | 0.181 | 0.144 | 0.187 | 0.023 | 0.067 | 0.023 | 0.067 | 0.096 | 0.139 |
| held-out test | Qwen2.5-7B-Instruct | B3 Triggered refusal | 0.215 | 0.257 | 0.230 | 0.272 | 0.212 | 0.254 | 0.209 | 0.251 | 0.023 | 0.067 | 0.190 | 0.233 | 0.223 | 0.265 |
| held-out test | Qwen2.5-7B-Instruct | B4 Universal reply | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 |
| held-out test | Qwen2.5-7B-Instruct | B5 Post-filter RAG | 0.109 | 0.152 | 0.088 | 0.131 | 0.001 | 0.045 | 0.023 | 0.067 | 0.023 | 0.067 | 0.128 | 0.171 | 0.023 | 0.067 |
| held-out test | Qwen2.5-7B-Instruct | B6 Typed collapse | 0.006 | 0.050 | 0.006 | 0.050 | 0.009 | 0.053 | 0.015 | 0.059 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 |
| held-out test | Llama-3.1-8B-Instruct | B0 Privileged agent | 0.211 | 0.253 | 0.211 | 0.253 | 0.194 | 0.237 | 0.118 | 0.161 | 0.023 | 0.067 | 0.023 | 0.067 | 0.131 | 0.174 |
| held-out test | Llama-3.1-8B-Instruct | B1 Privacy prompt | 0.243 | 0.285 | 0.220 | 0.262 | 0.164 | 0.207 | 0.206 | 0.248 | 0.023 | 0.067 | 0.023 | 0.067 | 0.102 | 0.145 |
| held-out test | Llama-3.1-8B-Instruct | B2 Output redaction | 0.323 | 0.364 | 0.323 | 0.364 | 0.234 | 0.276 | 0.180 | 0.223 | 0.023 | 0.067 | 0.023 | 0.067 | 0.131 | 0.174 |
| held-out test | Llama-3.1-8B-Instruct | B3 Triggered refusal | 0.187 | 0.230 | 0.186 | 0.229 | 0.210 | 0.252 | 0.185 | 0.228 | 0.023 | 0.067 | 0.190 | 0.233 | 0.203 | 0.245 |
| held-out test | Llama-3.1-8B-Instruct | B4 Universal reply | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 |
| held-out test | Llama-3.1-8B-Instruct | B5 Post-filter RAG | 0.106 | 0.149 | 0.097 | 0.140 | 0.029 | 0.073 | 0.070 | 0.114 | 0.023 | 0.067 | 0.128 | 0.171 | 0.001 | 0.045 |
| held-out test | Llama-3.1-8B-Instruct | B6 Typed collapse | 0.006 | 0.050 | 0.006 | 0.050 | 0.009 | 0.053 | 0.015 | 0.059 | 0.023 | 0.067 | 0.023 | 0.067 | 0.023 | 0.067 |
| certify split | Qwen2.5-7B-Instruct | L0 Universal reply, Template, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L0 Universal reply, Template, Post-filter | 0.097 | 0.133 | 0.073 | 0.109 | 0.040 | 0.076 | 0.081 | 0.116 | 0.003 | 0.039 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L0 Universal reply, Slot-restricted LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L0 Universal reply, Slot-restricted LLM, Post-filter | 0.093 | 0.128 | 0.063 | 0.098 | 0.002 | 0.038 | 0.081 | 0.116 | 0.003 | 0.039 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L0 Universal reply, Free LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L0 Universal reply, Free LLM, Post-filter | 0.093 | 0.128 | 0.069 | 0.105 | 0.029 | 0.065 | 0.081 | 0.116 | 0.003 | 0.039 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L1 Clarifier, Template, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L1 Clarifier, Template, Post-filter | 0.096 | 0.131 | 0.087 | 0.122 | 0.072 | 0.108 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L1 Clarifier, Slot-restricted LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L1 Clarifier, Slot-restricted LLM, Post-filter | 0.101 | 0.136 | 0.065 | 0.100 | 0.006 | 0.042 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L1 Clarifier, Free LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L1 Clarifier, Free LLM, Post-filter | 0.099 | 0.134 | 0.084 | 0.120 | 0.022 | 0.058 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L2 Clarifier and private action, Template, Pre-filter (selected: SameView) | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L2 Clarifier and private action, Template, Post-filter | 0.086 | 0.122 | 0.095 | 0.131 | 0.071 | 0.106 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L2 Clarifier and private action, Slot-restricted LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L2 Clarifier and private action, Slot-restricted LLM, Post-filter | 0.097 | 0.132 | 0.060 | 0.096 | 0.002 | 0.038 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L2 Clarifier and private action, Free LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L2 Clarifier and private action, Free LLM, Post-filter | 0.090 | 0.126 | 0.090 | 0.126 | 0.024 | 0.060 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L3 Leak notice (positive control), Template, Pre-filter | 0.167 | 0.202 | 0.148 | 0.183 | 0.177 | 0.212 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L3 Leak notice (positive control), Template, Post-filter | 0.272 | 0.306 | 0.257 | 0.291 | 0.254 | 0.288 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L3 Leak notice (positive control), Slot-restricted LLM, Pre-filter | 0.151 | 0.186 | 0.184 | 0.219 | 0.179 | 0.214 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L3 Leak notice (positive control), Slot-restricted LLM, Post-filter | 0.265 | 0.299 | 0.262 | 0.296 | 0.201 | 0.236 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L3 Leak notice (positive control), Free LLM, Pre-filter | 0.106 | 0.141 | 0.120 | 0.155 | 0.097 | 0.133 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Qwen2.5-7B-Instruct | L3 Leak notice (positive control), Free LLM, Post-filter | 0.199 | 0.234 | 0.211 | 0.245 | 0.139 | 0.175 | 0.072 | 0.108 | 0.019 | 0.054 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L0 Universal reply, Template, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L0 Universal reply, Template, Post-filter | 0.091 | 0.126 | 0.078 | 0.114 | 0.042 | 0.078 | 0.049 | 0.085 | 0.003 | 0.039 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L0 Universal reply, Slot-restricted LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L0 Universal reply, Slot-restricted LLM, Post-filter | 0.086 | 0.122 | 0.067 | 0.102 | 0.029 | 0.065 | 0.049 | 0.085 | 0.003 | 0.039 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L0 Universal reply, Free LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L0 Universal reply, Free LLM, Post-filter | 0.092 | 0.127 | 0.078 | 0.114 | 0.008 | 0.044 | 0.049 | 0.085 | 0.003 | 0.039 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L1 Clarifier, Template, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L1 Clarifier, Template, Post-filter | 0.104 | 0.139 | 0.094 | 0.129 | 0.073 | 0.109 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L1 Clarifier, Slot-restricted LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L1 Clarifier, Slot-restricted LLM, Post-filter | 0.097 | 0.133 | 0.061 | 0.096 | 0.050 | 0.086 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L1 Clarifier, Free LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L1 Clarifier, Free LLM, Post-filter | 0.133 | 0.169 | 0.085 | 0.120 | 0.017 | 0.052 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L2 Clarifier and private action, Template, Pre-filter (selected: SameView) | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L2 Clarifier and private action, Template, Post-filter | 0.099 | 0.135 | 0.091 | 0.127 | 0.078 | 0.114 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L2 Clarifier and private action, Slot-restricted LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L2 Clarifier and private action, Slot-restricted LLM, Post-filter | 0.109 | 0.144 | 0.060 | 0.096 | 0.050 | 0.086 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L2 Clarifier and private action, Free LLM, Pre-filter | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L2 Clarifier and private action, Free LLM, Post-filter | 0.125 | 0.161 | 0.058 | 0.094 | 0.023 | 0.059 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L3 Leak notice (positive control), Template, Pre-filter | 0.170 | 0.205 | 0.151 | 0.186 | 0.174 | 0.209 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L3 Leak notice (positive control), Template, Post-filter | 0.276 | 0.310 | 0.276 | 0.310 | 0.250 | 0.284 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L3 Leak notice (positive control), Slot-restricted LLM, Pre-filter | 0.057 | 0.092 | 0.110 | 0.145 | 0.091 | 0.126 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L3 Leak notice (positive control), Slot-restricted LLM, Post-filter | 0.150 | 0.185 | 0.179 | 0.214 | 0.174 | 0.209 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L3 Leak notice (positive control), Free LLM, Pre-filter | 0.005 | 0.041 | 0.028 | 0.064 | 0.023 | 0.059 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 | 0.003 | 0.039 |
| certify split | Llama-3.1-8B-Instruct | L3 Leak notice (positive control), Free LLM, Post-filter | 0.099 | 0.134 | 0.077 | 0.112 | 0.004 | 0.040 | 0.077 | 0.112 | 0.009 | 0.044 | 0.077 | 0.112 | 0.003 | 0.039 |

Note. One attacker (gradient boosting) per channel set, trained on the train split and frozen; advantage on one hash-picked world per unit. Held-out test rows are the baselines; certify-split rows are the 24 configurations.

## Table 9

Measured reply time and the timing attacker.

| Model | Configuration | Median reply time (s) | 99th percentile (s) | Longest (s) | Paired time difference, world 1 minus world 0 (s) | Paired time difference: Wilcoxon p | Paired token difference | Paired token difference: Wilcoxon p | Timing attacker, no floor: advantage | Timing attacker, no floor: upper bound | Timing attacker, 1 s floor: advantage | Timing attacker, 1 s floor: upper bound |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | L2 Clarifier and private action, Template, Pre-filter (selected: SameView) | 0.376 | 0.469 | 0.494 | 0.002 | 0.031 | 0.000 | 1.000 | 0.003 | 0.083 | 0.057 | 0.136 |
| Qwen2.5-7B-Instruct | L2 Clarifier and private action, Template, Post-filter | 0.371 | 0.463 | 0.502 | -0.002 | 0.642 | -1.813 | 0.000 | 0.003 | 0.083 | 0.057 | 0.136 |
| Qwen2.5-7B-Instruct | L2 Clarifier and private action, Free LLM, Pre-filter | 4.616 | 10.235 | 13.792 | -0.014 | 0.578 | -0.160 | 0.647 | 0.047 | 0.126 | 0.047 | 0.126 |
| Qwen2.5-7B-Instruct | L2 Clarifier and private action, Free LLM, Post-filter | 4.290 | 9.213 | 10.796 | -0.120 | 0.013 | -0.267 | 0.508 | 0.027 | 0.106 | 0.027 | 0.106 |
| Llama-3.1-8B-Instruct | L2 Clarifier and private action, Template, Pre-filter (selected: SameView) | 0.421 | 0.548 | 0.569 | -0.002 | 0.043 | 0.000 | 1.000 | 0.023 | 0.103 | 0.057 | 0.136 |
| Llama-3.1-8B-Instruct | L2 Clarifier and private action, Template, Post-filter | 0.412 | 0.544 | 0.568 | -0.002 | 0.482 | -1.867 | 0.000 | 0.010 | 0.090 | 0.057 | 0.136 |
| Llama-3.1-8B-Instruct | L2 Clarifier and private action, Free LLM, Pre-filter | 9.172 | 13.190 | 13.765 | 0.039 | 0.466 | -0.053 | 0.910 | 0.097 | 0.175 | 0.097 | 0.175 |
| Llama-3.1-8B-Instruct | L2 Clarifier and private action, Free LLM, Post-filter | 8.485 | 13.048 | 13.635 | -0.269 | 0.001 | -2.400 | 0.000 | 0.027 | 0.106 | 0.027 | 0.106 |

Note. Times measured live on one L4 GPU with fresh scores and fresh free-text wording (no caches). Paired difference: the same certify units in both worlds. With the 1 s floor every template reply takes exactly 1 s, so the attacker sees identical times and its accuracy equals the share of world-1 units among the 600 (advantage 0.057); the upper bound reflects the sample size, not a difference between the worlds. Free-text replies take 4 to 14 s, above the floor.

## Table 10

Domain 1 held-out test with seven attackers for the two main responders and a larger one.

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
| SameView (selected) | 0.023 | 0.023 | 0.024 | 0.977 | 0.987 | 0.983 |

## Table 11

The certificate over multi-turn sessions: the deployed configuration and the controls.

| Model | System | Role | Sessions | Attackers (policy, pool, learner) | Largest advantage | Upper bound (95%) | Certified bound | Certified at 0.10 |
|---|---|---|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | SameView (selected) | deployed configuration | 12000 | 24 | 0.039 | 0.083 | 0.080 | yes |
| Qwen2.5-7B-Instruct | SameView (selected) | deployed configuration | 12000 | 24 | 0.039 | 0.083 | 0.080 | yes |
| Llama-3.1-8B-Instruct | B1 Privacy prompt | control | 600 | 8 | 0.987 | 0.996 | 1.000 | no |
| Llama-3.1-8B-Instruct | B3 Triggered refusal | control | 900 | 12 | 0.947 | 0.973 | 0.980 | no |
| Llama-3.1-8B-Instruct | B5 Post-filter RAG | control | 1200 | 16 | 0.367 | 0.467 | 0.460 | no |
| Qwen2.5-7B-Instruct | B1 Privacy prompt | control | 600 | 8 | 1.000 | 1.000 | 1.000 | no |
| Qwen2.5-7B-Instruct | B3 Triggered refusal | control | 900 | 12 | 0.953 | 0.977 | 0.980 | no |
| Qwen2.5-7B-Instruct | B5 Post-filter RAG | control | 1200 | 16 | 0.360 | 0.460 | 0.450 | no |

Note. A session under one adaptive policy is a unit; each (policy, session pool, transcript learner after the last turn) is one frozen attacker. The deployed configuration is certified alone, so its share of delta is delta; the controls are tested the same way.
