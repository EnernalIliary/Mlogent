"""One conversion path for editable, delivered and decompiled logic.

Legacy CLI helpers delegate here. Signature and label implementations are
internal dependencies; the optional Mindcode backend is loaded only on demand.
"""
from __future__ import annotations

from . import signature as aigenerated
from .labels import LabelError, check_jump_targets, labelize, resolve, split_lines


def to_editable(text: str, prefix: str = "L", *, sign: bool = False):
    """Convert editable source, retaining attribution and payload on signed input."""
    hits = aigenerated._find(text)
    saved_labels = {}
    signed = bool(hits)
    if signed:
        problems = aigenerated.verify_text(text)
        if problems:
            raise aigenerated.SignError(problems[0])
        token = hits[0]
        author = token.group(1)
        comments, meta, saved_labels = aigenerated.decode_signature_payload(token.group(3))
        text = aigenerated._body(text)
    elif sign:
        author = aigenerated.DEFAULT_AUTHOR
        comments, meta = aigenerated.collect_comments(text), None

    out_text, total, njumps, labels = labelize(
        text, prefix, preferred_labels=saved_labels)
    signature = None
    if signed or sign:
        out_text, pid = aigenerated.sign_text(
            out_text, author, force=True, comments=comments, meta=meta,
            labels={target: name for target, name in saved_labels.items() if target < total})
        out_text, pid, _ = restore_comments(out_text)
        check_jump_targets(aigenerated._body(text), aigenerated._body(out_text))
        signature = (author, pid)
    return out_text, total, njumps, labels, signature


def to_delivery(text: str, author: str) -> tuple[str, str, int, int]:
    """Resolve editable labels and carry the first name per target in the payload."""
    hits = aigenerated._find(text)
    comments = meta = None
    saved_labels = {}
    if hits:
        if not aigenerated.verify_text(text):
            author = hits[0].group(1)
            comments, meta, saved_labels = aigenerated.decode_signature_payload(hits[0].group(3))
        # Strip the old token before resolving jumps: converting a label in a
        # signature-bearing tail jump to 0 can otherwise hide that instruction.
        if comments is None:
            comments = aigenerated.collect_comments(text)
        text = aigenerated._body(text)

    try:
        numeric, declarations, rewritten = resolve(text, strict=True)
    except LabelError as exc:
        raise aigenerated.SignError(str(exc)) from exc
    canonical = aigenerated._body(numeric)
    count = sum(bool(line.strip()) for line in canonical.splitlines())
    labels: dict[int, str] = {}
    for name, target in declarations.items():
        if target < count:
            labels.setdefault(target, name)
    if not declarations:
        labels = {target: name for target, name in saved_labels.items() if target < count}
    if comments is None:
        comments = aigenerated.collect_comments(text)
    signed, pid = aigenerated.sign_text(numeric, author, force=True, comments=comments, meta=meta, labels=labels)
    from .controlflow import difference
    if not difference(numeric, signed)["instruction_semantics_preserved"]:
        raise aigenerated.SignError("signing changed instruction semantics; delivery refused")
    return signed, pid, len(declarations), rewritten


def restore_comments(text: str) -> tuple[str, str, list[dict]]:
    """Restore statement-anchored comments and append one editable signature."""
    hits = aigenerated._find(text)
    if not hits:
        raise aigenerated.SignError("missing hidden @aigenerated argument")
    token = hits[0]
    comments = aigenerated.decode_comments(token.group(3))
    lines, kinds, total = split_lines(aigenerated._body(text))
    buckets = {}
    for comment in comments:
        anchor = min(max(comment["stmt"], 0), total)
        buckets.setdefault(anchor, []).append(comment)
    out = []
    statement = 0
    for line, (kind, index) in zip(lines, kinds):
        if line.strip():
            out.extend(c["text"] for c in buckets.pop(statement, []))
        out.append(line)
        if kind == "stmt":
            statement = index + 1
    out.extend(c["text"] for anchor in sorted(buckets) for c in buckets[anchor])
    payload = f":{token.group(3)}" if token.group(3) else ""
    out.append(f"# AI-Generated:Mlogent:{token.group(1)}:{token.group(2)}{payload}")
    return "\n".join(out) + "\n", token.group(2), comments


def _decompile_input(text: str) -> str:
    """Remove only token metadata, preserving every original instruction."""
    lines = []
    for line in text.splitlines():
        if aigenerated.SIG_COMMENT_RE.match(line.strip()):
            continue
        if aigenerated.SIG_RE.match(line.strip()):
            parts = aigenerated.SIG_PARTS_RE.match(line.strip())
            line = f"jump {parts.group(1)} always {parts.group(2)}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def extract(text: str, *, format: str = "mlog", timeout: float = 120.0):
    """Produce editable Mlog or a Mindcode draft without dropping control flow."""
    labelled, *_ = to_editable(text)
    if format == "mindcode":
        from mindcode import decompile_source

        return decompile_source(_decompile_input(labelled), timeout=timeout)
    return labelled, ""


def review(text: str) -> str:
    """Stable review form, with a raw fallback for a damaged signature."""
    try:
        labelled, _ = extract(text)
    except (ValueError, aigenerated.SignError):
        labelled = text
    return aigenerated._body(labelled) if aigenerated._find(labelled) else labelled


