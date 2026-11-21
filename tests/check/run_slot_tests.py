#!/usr/bin/env python3
"""Regression tests for command-specific operand slot classification."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import mlogcheck  # noqa: E402


def _rids(lines):
    return [(f.sev, f.rid, f.line) for f in mlogcheck.analyse(lines)]


def test_ucontrol_slots() -> None:
    target = _rids(["ucontrol target x y shoot", "end"])
    assert not any(rid == "undefined-var-read" and sev == "ERR"
                   for sev, rid, _line in target), target

    build = _rids(["ucontrol build x y @conveyor 0 0", "end"])
    assert not any(rid == "undefined-var-read" and sev == "ERR"
                   for sev, rid, _line in build), build


def test_select_reads_both_candidates() -> None:
    uses = mlogcheck.uses_of("select result lessThan lhs rhs first second")
    assert uses == ["lhs", "rhs", "first", "second"], uses


def test_color_pack_outputs_are_not_inputs() -> None:
    assert mlogcheck.uses_of("packcolor result r g b a") == ["r", "g", "b", "a"]
    assert mlogcheck.uses_of("unpackcolor r g b a value") == ["value"]


if __name__ == "__main__":
    test_ucontrol_slots()
    test_select_reads_both_candidates()
    test_color_pack_outputs_are_not_inputs()
    print("all run_slot_tests.py passed")
