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


if __name__ == "__main__":
    check_content_names_are_not_undefined()
    check_unknown_content_name_still_reports()
    print("all run_content_tests.py passed")
