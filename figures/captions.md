# Figure captions (drafts for the manuscript)

**Figure 1.** LoRe in three bands. The privileged band (top) holds the access lists, the full index, the permission controller (K1) and private actions such as filing an access request with a record's owner; it never replies to the user. The requester-view band (middle) is the only band that replies: it builds the requester's own index, where a forbidden record and a missing record give the same code (K2), scores the candidates and "none of these" with a conformal clarifier that answers, asks or gives one fixed reply (K3), and words the reply with a template or a slot-bound language model, a length bucket and a latency floor (K4). Restricted records never reach K3 or K4. The release band (bottom) runs offline before deployment: the built pipeline runs on paired worlds, a family of attackers is trained and frozen, a Learn-then-Test certificate bounds every attacker's advantage at ε with probability 1 − δ (K5), and the most useful certified configuration λ* is deployed.

File: `figure1_framework.png` and `figure1_framework.pdf`

**Figure 2.** The paired-world game. Both worlds give the requester the same permitted view; the protected fact (here, that a restricted Project Cedar memo exists) is true only in world 1. A coin picks the world, the built assistant answers the attacker's request, and the attacker guesses the world from everything it sees: text, options, error code, citations, length and time. The advantage is 0 when the reply says nothing about which world was drawn.

File: `figure2_paired_worlds.png` and `figure2_paired_worlds.pdf`

**Figure 3.** The Project Cedar example (Qwen2.5-7B-Instruct, Domain 1): three requests (rows) answered by four systems (columns) in both worlds. Orange frames mark replies that change with the hidden record. The privacy prompt (B1) states the restricted memo's contents or who can open it, or stops answering a request it answers in the other world; the triggered refusal (B3) refuses only when the restricted record exists, so the refusal itself is the leak. The universal reply (B4) and LoRe give the same reply in both worlds: B4 lists the permitted records that match, while LoRe asks which permitted record the user means and offers "none of these". Long replies are cut with an ellipsis.

File: `figure3_cedar_mechanism.png` and `figure3_cedar_mechanism.pdf`

**Figure 4.** Leakage against usefulness for the 24 configurations of Domain 1. Vertical axis: certified bound ε̂, the smallest ε certified with probability 0.95 against all six attackers on the certify split. Horizontal axis: share of mistyped and ambiguous requests resolved on the utility split. Shaded: certified at ε = 0.10. Every pre-filter configuration of levels L0 to L2 is certified; every post-filter configuration and every L3 positive control is rejected. The universal reply (L0) is certified but resolves about half of the requests; the ringed point is the selected configuration λ*. Points are shifted slightly sideways by wording and level so that they do not hide each other.

File: `figure4_frontier.png` and `figure4_frontier.pdf`

**Figure 5.** Advantage of each attacker (columns) against each system (rows) on held-out test units of Domain 1, for both models. Bold: the lower 95% bound is above 0.10. Systems above the line decide what to say from restricted data and leak; systems below the line decide from the permitted view only, and every attacker stays near zero.

File: `figure5_advantage_heatmap.png` and `figure5_advantage_heatmap.pdf`

**Figure 6.** Adaptive multi-turn attackers (Domain 1): accuracy of the best transcript learner against the number of turns (solid: Qwen2.5-7B-Instruct; dashed: Llama-3.1-8B-Instruct). The controls are the baselines each attack can succeed against: B1 for the attribute fact, B3 for existence and B5 for existence and membership. Against LoRe the transcripts are identical in both worlds at every turn, so accuracy stays at the share of world-1 units; against the controls, extra turns raise it.

File: `figure6_adaptive_attackers.png` and `figure6_adaptive_attackers.pdf`

**Figure 7.** Conformal clarifier on the Domain 1 test tasks: coverage of the intended option with its Wilson 95% band (left) and mean prediction-set size (right) against the miscoverage level α. Dashed: target 1 − α. Dotted: α = 0.10, used by LoRe. Coverage follows the target and the sets shrink as α grows.

File: `figure7_coverage.png` and `figure7_coverage.pdf`

**Figure 8.** Side channels of the clarifier with template wording (level L2), both models pooled, certify split. Left: reply length before padding; right: number of records cited. With pre-filter retrieval (top) the two worlds give the same distributions. With post-filter retrieval (bottom) a restricted record takes one of the five retrieval slots and is then removed, so in world 1 the reply never cites five records.

File: `figure8_side_channel.png` and `figure8_side_channel.pdf`
