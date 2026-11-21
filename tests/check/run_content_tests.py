#!/usr/bin/env python3
"""Regression tests for bare game-content declarations in mlogcheck."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import mlogcheck  # noqa: E402


def check_content_names_are_not_undefined() -> None:
    findings = mlogcheck.analyse([
        "jump dead always",
        "setblock block conveyor 0 0 @sharded 0",
        "dead:",
        "end",
    ])
    assert not any(f.rid == "undefined-var-read" for f in findings), findings
    assert [(f.sev, f.rid) for f in findings] == [("WARN", "unreachable-statement")], findings


def check_unknown_content_name_still_reports() -> None:
    findings = mlogcheck.analyse([
        "setblock block definitely_not_a_block 0 0 @sharded 0",
        "end",
    ])
    assert any(f.rid == "undefined-var-read" for f in findings), findings

    wrong_case = mlogcheck.analyse([
        "setblock block Conveyor 0 0 @sharded 0",
        "end",
    ])
    assert any(f.rid == "undefined-var-read" for f in wrong_case), wrong_case


def check_decorative_jump_does_not_kill_fallthrough() -> None:
    findings = mlogcheck.analyse(["jump -1 always", "set x 1", "end"])
    assert not any(f.rid == "unreachable-statement" for f in findings), findings


def check_invalid_jump_condition_does_not_add_branch() -> None:
    findings = mlogcheck.analyse([
        "jump 2 notACondition x 0",
        "stop",
        "set x 1",
    ])
    assert [(f.sev, f.rid, f.line) for f in findings
            if f.rid == "unreachable-statement"] == [("WARN", "unreachable-statement", 2)], findings


def check_mindcode_generated_unreachable_noise_is_ignored() -> None:
    findings = mlogcheck.analyse([
        "jump 2 always",
        "set *tmp0 null",
        "end",
        'print "Compiled by Mindcode 3.19.3 - github.com/cardillan/mindcode"',
    ])
    assert not any(f.rid == "unreachable-statement" for f in findings), findings


def check_user_unreachable_statements_still_report() -> None:
    findings = mlogcheck.analyse([
        "jump 3 always",
        "set user_state null",
        "end",
        "print user_state",
    ])
    assert any(f.rid == "unreachable-statement" for f in findings), findings


if __name__ == "__main__":
    check_content_names_are_not_undefined()
    check_unknown_content_name_still_reports()
    check_decorative_jump_does_not_kill_fallthrough()
    check_invalid_jump_condition_does_not_add_branch()
    check_mindcode_generated_unreachable_noise_is_ignored()
    check_user_unreachable_statements_still_report()
    print("all run_content_tests.py passed")
