"""Localisation store + gate invariants (Track 3, #21). Run: python -m pytest tests/unit/test_localization_gate.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "DataEngine" / "localization"))
from gate import check, load_store, select_strategy  # noqa: E402

STORE = load_store()
WB_ZONES = {"north_bengal_tea_belt", "gangetic_plain", "rarh_plateau", "sundarbans_delta", "kolkata_metro", "medinipur_coastal"}


def test_every_wb_zone_exists_and_all_23_districts_are_mapped():
    assert WB_ZONES <= set(STORE["zones"])
    assert len(STORE["district_zone_map"]) == 23


def test_entities_reference_known_zones_and_have_bengali_names():
    for e in STORE["entities"].values():
        assert e.get("zones"), e["id"]
        for z in e["zones"]:
            assert z in STORE["zones"], (e["id"], z)
    wb = [e for e in STORE["entities"].values() if set(e["zones"]) & WB_ZONES]
    assert len(wb) >= 40
    assert all(e.get("name_bn") for e in wb)


def test_every_approved_substitution_passes_the_gate():
    failures = {sid: check(s, STORE)["reasons"] for sid, s in STORE["substitutions"].items()
                if s.get("status") == "approved" and not check(s, STORE)["ok"]}
    assert not failures, failures


def test_documented_traps_are_blocked():
    for rej in STORE["rejected_examples"]:
        c = STORE["concepts"].get(rej.get("concept_id")); e = STORE["entities"].get(rej["local_anchor"]["entity_id"])
        if c and e:
            assert select_strategy(c, e) is None, rej["id"]


def test_kite_cannot_anchor_gravity_and_matka_cannot_anchor_heat():
    kite = STORE["entities"]["kite"]; matka = STORE["entities"]["matka"]
    assert select_strategy(STORE["concepts"]["c_gravity"], kite) is None
    assert select_strategy(STORE["concepts"]["c_evapcool"], matka) == "anchor_substitution"


def test_analogies_carry_disanalogy_flags_and_keep_the_exam_term():
    for s in STORE["substitutions"].values():
        if s.get("strategy") == "analogy":
            assert s.get("disanalogy_flags"), s["id"]
        assert s.get("keep_canonical") is True, s["id"]
        if s.get("text_bn"):
            c = STORE["concepts"][s["concept_id"]]
            keys = [c["exam_term_bn"]] + c["name_bn"].split()
            assert any(k[:4] in s["text_bn"] for k in keys if len(k) >= 3), (s["id"], keys)
