"""Central config. Paths, sizes, models, systems, attackers and pre-registered constants live here; notebooks
import them and never hardcode them. Plan v1 (15 Nov 2026) is docs/plan_v1.md."""
import os
from pathlib import Path

PROJECT = "REFUSELEAK"
REPO_NAME = "refuseleak-research"
GH_USER = "anasbiswas1"

DRIVE_ROOT = Path(os.environ.get("REFUSELEAK_DRIVE_ROOT", f"/content/drive/MyDrive/{PROJECT}_Research"))
REPO_DIR = Path(os.environ.get("REFUSELEAK_REPO_ROOT", str(DRIVE_ROOT / REPO_NAME)))

NOTEBOOKS = REPO_DIR / "notebooks"
SRC = REPO_DIR / "src"
REPORTS = REPO_DIR / "reports"
FIGURES = REPO_DIR / "figures"
DOCS = REPO_DIR / "docs"
DATA = REPO_DIR / "data"                 # gitignored: model caches, dry-run records
EXTERNAL = REPO_DIR / "external"         # gitignored
SUITE_DATA = REPO_DIR / "suite_data"     # committed: paraphrase pool, unit manifests
RECORDS = REPORTS / "02_records"         # committed: every recorded observation of the probe, gzipped JSON lines

RUNTIME_VERSION = "3"   # bumped whenever prompts, systems or the harness change; observations of an older runtime are re-run (2: person names never count as record names, filler words dropped from body matching, owner-name secret-string rule;
                        # 3: a request that names a permitted record is never refused outright, the clarifier asks instead (Equation 13 as amended with notebook 07d))
WORLD_VERSION = "2"     # bumped whenever the world generator changes; part of every unit id (2: all four sensitive types as confidential anchors, type-aware S2 and S3 queries, HR department)

# ----------------------------------------------------------------------------- world (plan v1, Section 9.1)
SEED = 20261115
COMPANY = "Meridian Holdings"
DEPARTMENTS = ["Finance", "Legal", "HR", "Engineering", "Operations", "Sales", "Marketing", "IT"]
RECORD_TYPES = ["project_brief", "investigation", "hr_case", "acquisition_memo", "vendor_contract", "support_ticket"]
SENSITIVE_TYPES = ["investigation", "hr_case", "acquisition_memo", "project_brief"]   # restricted targets are drawn from these
PEOPLE_PER_WORLD = 48
RECORDS_PER_TYPE = {"project_brief": 20, "investigation": 8, "hr_case": 8, "acquisition_memo": 8,
                    "vendor_contract": 26, "support_ticket": 30}
N_DECOYS = 2                      # permitted records that share the restricted record's code-name token
SECRET_TYPES = ["S1", "S2", "S3"]  # existence, membership, attribute
LEAK_FAMILIES = {"S1": ["Q1", "Q2", "Q4", "Q5", "Q6", "Q7"], "S2": ["Q3", "Q3b"], "S3": ["Q1a", "Q2a"]}
S2_ANCHOR_TYPES = ["investigation", "hr_case"]   # membership secrets are about case teams
LEGIT_FAMILIES = ["Q4", "Q5"]     # legitimate tasks with a known permitted target (P1)
AUTH_FAMILY = "Q8"                # authorised requests, over-refusal check

# ----------------------------------------------------------------------------- unit splits (unit ids are deterministic)
SPLITS = {"probe": 600, "legit": 300, "auth": 200,           # notebook 02
          "train": 2000, "calibration": 3000, "utility": 1000, "test": 2000,   # notebooks 03 onward
          "certify": 3000}          # notebook 04 onward: the certificate's units (the calibration split fitted the clarifier)

# ----------------------------------------------------------------------------- systems and harness
TOP_K = 5                         # records in a responder's context, and candidates for template systems
MATCH_THRESHOLD = 0.5             # name match (character-bigram Dice) above which a record counts as a candidate
MAX_TURNS = 3                     # clarification turns before a legitimate task counts as failed
MAX_TOKENS = 200
TEMPERATURE = 0.0
LATENCY_BUCKET_S = 0.25
WORKERS = 48
BASELINES = ["B0", "B1", "B2", "B3", "B4", "B5", "B6", "O1", "O2"]
LLM_SYSTEMS = {"B0", "B1", "B2", "B3", "B5"}          # B2 reuses B0's generation; B3 calls the model only when not triggered
SIDE_FEATURES = ["n_chars", "n_tokens", "n_cites", "n_options", "latency_bucket", "status_code"]

MODELS = {
    "qwen25_7b": "Qwen/Qwen2.5-7B-Instruct",
    "llama31_8b": "meta-llama/Llama-3.1-8B-Instruct",
}
SCALE_MODELS = {                  # notebook 14: a larger responder on the Domain 1 held-out test (not part of the main grid)
    "qwen25_14b": "Qwen/Qwen2.5-14B-Instruct-AWQ",
}
EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"             # attacker D2
NLI_MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"       # attacker D3 and the disclosure judge
ATTACKERS = ["D1", "D2", "D3", "D5"]
N_FOLDS = 5

# ----------------------------------------------------------------------------- clarifier (plan v1, Section 6.5)
CANDIDATES_M = 5                  # permitted candidates offered to the scorer, plus "none of these"
MAX_LIST_OPTIONS = 4              # a set larger than this is narrowed by an attribute question first (Equation 14)
CLARIFIER_ATTRIBUTES = ["type", "dept", "owner"]
LORE = "LORE"                     # system id of the low-view conformal clarifier (method name is a placeholder)
TIE_STRATA = 4                    # conformal threshold per tie size (candidates sharing the best name match), capped here
MIN_STRATUM = 50                  # a stratum with fewer threshold-half points uses the pooled threshold
SCORER = "combined"               # the method's conformity score: permitted-view evidence plus the model's option log-probability
LORE_ABLATIONS = {"LORE-E": "evidence", "LORE-L": "llm"}   # same mechanism, evidence-only and model-only scores

# ----------------------------------------------------------------------------- configuration space (plan v1, Section 7.3)
LEVELS = ["L0", "L1", "L2", "L3"]        # universal reply only; + clarification; + private access routing; + explicit restricted-match notice (positive control)
RENDERS = ["RT", "RS", "RF"]             # template; model rewrite restricted to low-view slots (greedy); free model wording (temperature 0.7)
RETRIEVALS = ["pre", "post"]             # candidates from the permitted index; top-m over the full index with restricted records dropped
RENDER_TEMPERATURE = {"RS": 0.0, "RF": 0.7}
RENDER_MAX_TOKENS = 160
LENGTH_BUCKET_CHARS = 160                # reply text padded to a multiple of this
MAX_REPLY_CHARS = 1120                   # seven buckets; longer text is cut first
LATENCY_FLOOR_S = 1.0                    # every reply is held to this latency (one bucket for all reply kinds)
CERT_SPLITS = {"train": "train", "certify": "certify", "test": "test", "utility": "utility", "legit": "legit", "auth": "auth"}

# ----------------------------------------------------------------------------- Domain 2 (Enron, notebook 07)
ENRON_SPLITS = {"calibration": 1500, "utility": 500, "train": 1000, "certify": 2000, "test": 1000, "legit": 300, "auth": 200}
ENRON_NONE_SAMPLE = {"calibration": 500, "test": 300}        # restricted-target tasks for the clarifier's threshold and its test:
# one per legitimate task in both (500 and 500; 300 and 300), as in Domain 1, so the test tasks are drawn as the
# calibration tasks were. Notebook 07b drew 150 (one per two legitimate tasks); notebook 07c corrects the draw.
AGENTDOJO_VERSION = "0.1.34"                                  # pinned as in agent-trust-research
AGENT_SPLITS = {"train": 500, "test": 2000, "legit": 300, "auth": 100}   # notebook 08: leak units (S1 and S3 alternate), legitimate (exact,
# variant, typo names in turn) and authorised (a sensitive-topic file shared with the requester) tasks
AGENT_MAX_ITERS = 4                                            # tool rounds per conversation
AGENT_MAX_TOKENS = 200                                         # generation stops at the closing tag of a tool call (notebook 08b)
ENRON_FRESH = {"legit": (300, 300), "auth": (200, 200)}   # (first index, count): legitimate and authorised units never seen before notebook 07d,
# drawn as the legit and auth splits were (same split names, later indices); utility is read on them because the amended rule was found on legit 0 to 299
ENRON_CONFIGS = ["L0-RT-pre", "L1-RT-pre", "L2-RT-pre", "L3-RT-pre", "L0-RT-post", "L1-RT-post", "L2-RT-post", "L3-RT-post",
                 "L2-RS-pre", "L2-RF-pre"]                  # the eight decision configurations and the rendered variants of the selected level

# ----------------------------------------------------------------------------- adaptive attackers (notebook 09)
ADAPTIVE_UNITS = {"train": (2000, 1500), "test": (2000, 6000)}   # (first index, count) of fresh Domain 1 units, never used before notebook 09:
# 500 training and 2,000 test units per secret type (build_unit gives index i the secret SECRET_TYPES[i % 3])
ADAPTIVE_BASELINE_UNITS = 300           # the language-model baselines run on the first 300 training and 300 test units of each secret type
ADAPTIVE_BASELINES = {"S1": ["B3", "B5"], "S2": ["B5"], "S3": ["B1"]}   # the baselines that can leak each secret: B3 only existence (its trigger), B5 existence
# and membership (restricted records take retrieval slots), B1 every secret (privileged context); B3 and B5 cannot leak an attribute by construction
ADAPTIVE_MAX_FOLLOW = 2                 # follow-up replies A4 reads after answering "none of these"

# ----------------------------------------------------------------------------- side channels (notebook 10)
SIDE_TIMING_UNITS = {"train": 200, "certify": 600}   # the first units of each split, both worlds, timed on the L4
SIDE_TIMING_CONFIGS = ["L2-RT-pre", "L2-RT-post", "L2-RF-pre", "L2-RF-post"]
SIDE_TIMING_WORKERS = {"RT": 8, "RF": 16}           # requests in flight: template decisions, then free-text renders

# ----------------------------------------------------------------------------- pre-registered (plan v1, Sections 6 and 11)
EPSILON = 0.10
DELTA = 0.05
ALPHA = 0.10
PROBE = {"P0": {"systems": ["B0", "B1", "B2", "B3", "B5"], "min_systems": 2, "adv_lower_bound": 0.10, "all_models": True},
         "P1": {"system": "B4", "oracle": "O1", "families": LEGIT_FAMILIES, "min_gap": 0.10},
         "P2": {"system": "B4", "adv_lower_bound_must_be": 0.0}}


def ensure_dirs():
    for p in (NOTEBOOKS, SRC, REPORTS, FIGURES, DOCS, DATA, EXTERNAL, SUITE_DATA, RECORDS):
        p.mkdir(parents=True, exist_ok=True)


def preregistration() -> dict:
    return {
        "plan": "When Refusal Reveals, research and implementation plan v1 (15 Nov 2026), docs/plan_v1.md",
        "seed": SEED, "world_version": WORLD_VERSION, "runtime_version": RUNTIME_VERSION,
        "people_per_world": PEOPLE_PER_WORLD, "records_per_type": RECORDS_PER_TYPE, "decoys": N_DECOYS,
        "secret_types": SECRET_TYPES, "leak_families": LEAK_FAMILIES, "legit_families": LEGIT_FAMILIES,
        "splits": SPLITS, "top_k": TOP_K, "match_threshold": MATCH_THRESHOLD, "max_turns": MAX_TURNS,
        "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE, "models": MODELS, "embedder": EMBEDDER,
        "nli_model": NLI_MODEL, "baselines": BASELINES, "attackers": ATTACKERS, "n_folds": N_FOLDS,
        "epsilon": EPSILON, "delta": DELTA, "alpha": ALPHA, "probe": PROBE,
        "levels": LEVELS, "renders": RENDERS, "retrievals": RETRIEVALS, "length_bucket_chars": LENGTH_BUCKET_CHARS,
        "latency_floor_s": LATENCY_FLOOR_S,
    }
