"""CPU tests that each domain keeps its own word lists: the email words of Domain 2 (never record names there) and its
email type words do not reach Domain 1, whose lists stay as measured in notebooks 02 to 06."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import clarifier as CL  # noqa: E402
import index as IX  # noqa: E402

EMAIL_WORDS = {"email", "thread", "message", "legal", "personal", "business", "urgent", "restricted"}


def test_generic_lists_are_per_domain():
    assert not EMAIL_WORDS & IX.generic_of(None)
    assert EMAIL_WORDS <= IX.generic_of("enron")
    assert IX.GENERIC <= IX.GENERIC_ENRON


def test_record_names_follow_the_record_domain():
    d1 = {"ref": "MH-0001", "title": "Legal Holds Review", "codename": None}
    d2 = {"ref": "EN-0001", "title": "Legal Holds Review", "codename": None}
    assert "legal" in IX.name_tokens(d1)
    assert "legal" not in IX.name_tokens(d2)
    assert IX.name_match(d1, "the legal file") == 1.0
    assert IX.name_match(d2, "the legal file") == 0.0


def test_has_name_reads_the_world_domain():
    world1 = {"people": [{"first": "Ann", "last": "Lee"}]}
    world2 = {"people": [{"first": "Ann", "last": "Lee"}], "domain": "enron"}
    assert IX.has_name(world1, "open the personal note")
    assert not IX.has_name(world2, "open the personal email")


def test_type_words_per_domain():
    assert not CL.any_type_word("forward the email", None)
    assert CL.any_type_word("forward the email", "enron")
    assert CL.any_type_word("the vendor contract", None) and CL.any_type_word("the vendor contract", "enron")
