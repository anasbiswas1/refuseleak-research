# Figure captions (drafts for the manuscript)

**Figure 1.** SameView in three bands. The privileged band (top) holds the access lists, the full index, the permission controller (K1) and private actions such as filing an access request with a record's owner; it never replies to the user. The requester-view band (middle) is the only band that replies: it builds the requester's own index, where a forbidden record and a missing record give the same code (K2), scores the candidates and "none of these" with a conformal clarifier that answers, asks or gives one fixed reply (K3), and words the reply with a template or a slot-bound language model, a length bucket and a latency floor (K4). Restricted records never reach K3 or K4. The release band (bottom) runs offline before deployment: the built pipeline runs on paired worlds, a family of attackers is trained and frozen, a Learn-then-Test certificate bounds every attacker's advantage at ε with probability 1 − δ (K5), and the most useful certified configuration λ* is deployed.

File: `figure1_framework.png` and `figure1_framework.pdf`

**Figure 2.** The paired-world game. Both worlds give the requester the same permitted view; the protected fact (here, that a restricted Project Cedar memo exists) is true only in world 1. A coin picks the world, the built assistant answers the attacker's request, and the attacker guesses the world from everything it sees: text, options, error code, citations, length and time. The advantage is 0 when the reply says nothing about which world was drawn.

File: `figure2_paired_worlds.png` and `figure2_paired_worlds.pdf`

**Figure 3.** The Project Cedar example (Qwen2.5-7B-Instruct, Domain 1): three requests (rows) answered by four systems (columns) in both worlds. Orange frames mark replies that change with the hidden record. The privacy prompt (B1) states the restricted memo's contents or who can open it, or stops answering a request it answers in the other world; the triggered refusal (B3) refuses only when the restricted record exists, so the refusal itself is the leak. The universal reply (B4) and SameView give the same reply in both worlds: B4 lists the permitted records that match, while SameView asks which permitted record the user means and offers "none of these". Long replies are cut with an ellipsis.

File: `figure3_cedar_mechanism.png` and `figure3_cedar_mechanism.pdf`

**Figure 4.** Leakage against usefulness for the 24 configurations of Domain 1. Vertical axis: certified bound ε̂, the smallest ε certified with probability 0.95 against all seven attackers on the certify split. Horizontal axis: share of mistyped and ambiguous requests resolved on the utility split. Shaded: certified at ε = 0.10. Every pre-filter configuration of levels L0 to L2 is certified; every post-filter configuration and every L3 positive control is rejected. The universal reply (L0) is certified but resolves about half of the requests; the ringed point is the selected configuration λ*. Points are shifted slightly sideways by wording and level so that they do not hide each other.

File: `figure4_frontier.png` and `figure4_frontier.pdf`

**Figure 5.** Advantage of each attacker (columns) against each system (rows) on held-out test units of Domain 1, for both models. Bold: the lower 95% bound is above 0.10. Systems above the line decide what to say from restricted data and leak; systems below the line decide from the permitted view only, and every attacker stays near zero.

File: `figure5_advantage_heatmap.png` and `figure5_advantage_heatmap.pdf`

**Figure 6.** Adaptive multi-turn attackers (Domain 1): accuracy of the best transcript learner against the number of turns (solid: Qwen2.5-7B-Instruct; dashed: Llama-3.1-8B-Instruct). The controls are the baselines each attack can succeed against: B1 for the attribute fact, B3 for existence and B5 for existence and membership. Against SameView the transcripts are identical in both worlds at every turn, so accuracy stays at the share of world-1 units; against the controls, extra turns raise it.

File: `figure6_adaptive_attackers.png` and `figure6_adaptive_attackers.pdf`

**Figure 7.** Conformal clarifier on the Domain 1 test tasks: coverage of the intended option with its Wilson 95% band (left) and mean prediction-set size (right) against the miscoverage level α. Dashed: target 1 − α. Dotted: α = 0.10, used by SameView. Coverage follows the target and the sets shrink as α grows.

File: `figure7_coverage.png` and `figure7_coverage.pdf`

**Figure 8.** Side channels of the clarifier with template wording (level L2), both models pooled, certify split. Left: reply length before padding; right: number of records cited. With pre-filter retrieval (top) the two worlds give the same distributions. With post-filter retrieval (bottom) a restricted record takes one of the five retrieval slots and is then removed, so in world 1 the reply never cites five records.

File: `figure8_side_channel.png` and `figure8_side_channel.pdf`

**Figure 9.** The certificate against the number of certify units, from random subsets of the stored per-unit guesses of all seven attackers (200 subsets per size, drawn without replacement; the largest size is the full split and gives the certificate of Table 3). Left: median certified bound, with its 10th to 90th percentile band in Domain 1. Right: share of configurations certified at ε = 0.10; post-filter configurations and the L3 positive control are never certified (drawn just above and below zero). Dotted lines: the size Equation 19 gives for 80% power against one attacker at chance (1,375 units in Domain 1 at δ/24; 1,168 in Domain 2 at δ/10). Solid: Domain 1 (24 configurations); dashed: Domain 2 (10 configurations).

File: `figure9_sensitivity.png` and `figure9_sensitivity.pdf`

**Figure 10.** The leak by query family: the advantage of each system's strongest attacker (the one of Table 7, chosen on the whole held-out split) read per query family (columns) and system (rows) in Domain 1, for both models. Bold: the lower 95% bound is above 0.10; grey: the lower bound is zero. Families have 110 to 330 test units each, so the intervals are wider than in Figure 5. Systems above the line decide from restricted data, and where they leak depends on the request: the triggered refusal and the full-view clarifier leak when the request names the record (Q1, Q4, Q5, Q7) and not when it asks about a person or an attribute; the privileged agent and the privacy prompt leak on nearly every family. Systems below the line stay at the floor in every family: the values repeated down a column of the lower block are that family's share of world-1 units, which is what a constant guess scores.

File: `figure10_family_heatmap.png` and `figure10_family_heatmap.pdf`
