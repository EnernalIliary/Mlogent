"""Remove only known editor placeholders from provably unused trailing slots.

Other names can intentionally declare variables. Never shift instructions,
remove interior operands, or rewrite a signature-bearing program.
"""
from __future__ import annotations
from functools import lru_cache
import json

from ..paths import TOOLS_ROOT

DEFAULT_PLACEHOLDERS = frozenset({"true", "false", "a", "b"})


@lru_cache(maxsize=1)
def _specs():
    with (TOOLS_ROOT / "instr_semantics.json").open(encoding="utf-8") as stream:
        return json.load(stream)["instructions"]


def clean(text: str) -> tuple[str, list[dict]]:
    import mlogcheck
    from . import signature

    if signature._find(text):
        return text, []
    output, changes = [], []
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        stripped = body.strip()
        if (not stripped or "#" in body or ";" in body
                or "AI-Generated:Mlogent:" in body):
            output.append(line)
            continue
        tokens = mlogcheck.tokenize(stripped)
        spec = _specs().get(tokens[0]) if tokens else None
        if not spec:
            output.append(line)
            continue
        used = set(spec.get("defs", [])) | set(spec.get("uses", []))
        used.update(int(index) for index in spec.get("tokens", {}))
        if tokens[0] == "jump" and len(tokens) >= 3 and tokens[2] == "always":
            used = {0, 1}  # destination and condition; both compare slots are ignored.
        elif tokens[0] == "op":
            if len(tokens) < 2 or tokens[1] not in mlogcheck.OP_UNARY | mlogcheck.OP_BINARY:
                output.append(line)
                continue
            used = {0, 1, 2} if tokens[1] in mlogcheck.OP_UNARY else {0, 1, 2, 3}
        elif spec.get("subcommands"):
            sub = spec["subcommands"].get(tokens[1]) if len(tokens) > 1 else None
            if sub is None:
                output.append(line)
                continue
            used = set(spec.get("defs", [])) | set(sub.get("defs", []))
            used.update(sub.get("semantic_uses", sub.get("uses", [])))
            used.update(int(index) for index in spec.get("tokens", {}))
            used.add(0)  # subcommand selector
        # Argument indices exclude the mnemonic. Keep every position up to the
        # last meaningful field; leave missing fields alone rather than fill them.
        keep = max(used, default=-1) + 2
        removed = []
        while len(tokens) > keep and tokens[-1] in DEFAULT_PLACEHOLDERS:
            token = tokens.pop()
            body = body.rstrip()
            body = body[:-len(token)].rstrip()
            removed.insert(0, token)
        if removed:
            changes.append({"line": number, "removed": removed})
        output.append(body + ending if removed else line)
    return "".join(output), changes
