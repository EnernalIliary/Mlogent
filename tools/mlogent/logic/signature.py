"""Signature recognition, canonical body hashing and safe-slot mounting."""
import hashlib
import json
import os
import re

from .labels import LABEL_NAME_RE as LABEL_NAME, LABEL_RE as _LABEL_LINE
from .payload import (
    SignError, PAYLOAD_V, META_KEYS, _meta_text, meta_of_job,
    encode_comments, decode_signature_payload, decode_payload, decode_comments, decode_meta,
)
from .slots import find_slot


DEFAULT_AUTHOR = "MAI"
PROJECT_NAME = "Mlogent"
PROJECT_VERSION = os.environ.get("MLOGENT_VERSION", "1.9.2")
PROJECT_REPO = "https://github.com/EnernalIliary/Mlogent"
# the sidecar (tools/logicd.py, tools/jobqueue.py) signs with this one; the
# environment override exists so a build can attribute a different author
SIGN_AUTHOR = os.environ.get("MAI_SIGN_AUTHOR") or DEFAULT_AUTHOR
SIG_LINE = 'jump 0 always 0 "AI-Generated:Mlogent:{author}:{pid}{payload}"'
# addr/value are not captured: author/id/payload stay at groups 1/2/3
SIG_RE = re.compile(
    r'^jump\s+\S+\s+always\s+\S+\s+"AI-Generated:Mlogent:([^":]+):([0-9a-f]{12})'
    r'(?::([A-Za-z0-9_-]+))?"\s*$')
SIG_COMMENT_RE = re.compile(
    r'^#\s*AI-Generated:Mlogent:([^":]+):([0-9a-f]{12})'
    r'(?::([A-Za-z0-9_-]+))?\s*$')
SIG_PARTS_RE = re.compile(r'^jump\s+(\S+)\s+always\s+(\S+)\s+"AI-Generated:Mlogent:')
# older releases used a comment header + unreachable set; drop those on re-sign
OLD_MARK_RE = re.compile(
    r"^(?:# @aigenerated(?:-end)?\b.*|set aigenerated\.[0-9a-f]{12}\b.*)$")
# release 0.9 put the token after `end`; normalise that back to a plain `end`
OLD_TAIL_RE = re.compile(r'^end\s+"AI-Generated:Mlogent:[^"]*"\s*$')


def _clean(text: str) -> list[str]:
    """Normalise newlines and drop every existing signature / legacy mark."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out = []
    for line in text.split("\n"):
        if line.strip().startswith("#"):
            continue
        if SIG_RE.match(line.strip()):
            m = SIG_PARTS_RE.match(line.strip())
            if m:
                # Signature always occupies an existing jump's compare slot.
                out.append(f"jump {m.group(1)} always {m.group(2)}")
            continue
        if OLD_MARK_RE.match(line):
            continue
        if OLD_TAIL_RE.match(line.strip()):
            out.append("end")
            continue
        out.append(line)
    return out


def _canonical(lines: list[str]) -> str:
    """Signature-free body, guaranteed to end with a single `end`."""
    lines = list(lines)
    while lines and not lines[-1].strip():
        lines.pop()
    last = -1
    for i in range(len(lines) - 1, -1, -1):
        s = lines[i].strip()
        if s and not s.startswith("#"):
            last = i
            break
    if last < 0:
        return ""
    trailing = [l for l in lines[last + 1:] if l.strip().startswith("#")]
    head = lines[:last + 1]
    if head[last].strip() == "end":
        head = head[:last]
    return "\n".join(head + trailing + ["end"]) + "\n"


def _body(text: str) -> str:
    return _canonical(_clean(text))


def collect_comments(text: str) -> list[dict]:
    """Comments with their original 1-based line and statement anchor.

    `stmt` is the number of statements before the comment; label lines do not
    count, so the anchor survives `resolve_labels` and re-labelling.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[dict] = []
    stmt = 0
    for no, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            if SIG_COMMENT_RE.match(s):
                continue
            out.append({"line": no, "stmt": stmt, "text": s})
            continue
        if _LABEL_LINE.match(line):
            continue
        stmt += 1
    return out


def project_meta(author: str) -> dict:
    return {"tool": PROJECT_NAME, "version": PROJECT_VERSION,
            "repo": PROJECT_REPO, "author": author}


def _hash(author: str, body: str, labels: dict[int, str] | None = None) -> str:
    material = author + "\n" + body
    if labels:
        material += "\0labels\0" + json.dumps(sorted(labels.items()), separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _find(text: str):
    text = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    hits = []
    for ln in text.split("\n"):
        m = SIG_RE.match(ln.strip()) or SIG_COMMENT_RE.match(ln.strip())
        if m:
            hits.append(m)
    return hits


def sign_text(text: str, author: str = DEFAULT_AUTHOR, force: bool = False,
              comments: list[dict] | None = None, meta: dict | None = None,
              *, labels: dict[int, str] | None = None):
    """Return (signed_text, id).  Raises SignError if it would change an id.

    Comments are moved into the signature string (base64 payload), so the
    delivered code carries them without occupying lines: no `#` line survives in
    the signed text (the game's assembler drops them, and `b.code` is rebuilt from
    the assembled program, so a kept one would look like a write that never
    landed). The id hashes the canonical code body and saved label table.
    """
    hits = _find(text)
    body = _body(text)
    # Empty input has no existing instruction on which to mount a signature.
    if not body and not hits:
        raise SignError("no statement to attach the signature to")
    author = re.sub(r'[:"]', "", author).strip() or DEFAULT_AUTHOR
    # Scan backwards for an existing unconditional jump with an unused compare
    # slot. Preserve the jump and all following statements. Spell out a missing
    # unused value operand before hashing so verification rebuilds the same body.
    lines = body.rstrip("\n").split("\n") if body else [""]
    # comments travel in the signature payload, never as lines of the delivered
    # code: the game's assembler drops `#` lines, and `b.code` -- which the mod
    # compares with the job's code character by character -- is rebuilt from the
    # assembled program, so a kept comment line would read as "the write did not
    # land". The id covers the code body and, when present, the label table.
    lines = [l for l in lines if not l.strip().startswith("#")]
    slot = find_slot(lines)
    if slot is not None and slot.added_value:
        lines[slot.index] = slot.prefix
        body = "\n".join(lines) + "\n"
    old, old_meta, old_labels = decode_signature_payload(hits[0].group(3)) if hits else ([], None, {})
    if labels is None:
        # Anchors from a modified body cannot be safely reused.
        labels = old_labels if old_labels and not verify_text(text) else {}
    pid = _hash(author, body, labels)[:12]
    if hits:
        old_id, old_author = hits[0].group(2), hits[0].group(1)
        if old_id == pid and old_author == author and not force:
            return text, pid
        if (old_id != pid or old_author != author) and not force:
            raise SignError(
                f"body changed since signing (id {old_id} -> {pid}); "
                f"pass --force to re-sign")
    cs = collect_comments(text) if comments is None else comments
    # 重签没显式给 meta 就把旧的带过来：上下文跟着代码走，不该因为一次重签丢掉
    merged_meta = project_meta(author)
    if old_meta:
        merged_meta.update(old_meta)
    if meta:
        merged_meta.update(meta)
    meta = merged_meta
    if comments is None and old:
        if len(cs) == len(old):
            # keep the original line numbers, refresh the text/anchors
            for o, c in zip(old, cs):
                c["line"] = o["line"]
        else:
            cs = old
    enc = encode_comments(cs, meta, labels=labels)
    payload = f":{enc}" if enc else ""
    sig = f'"AI-Generated:Mlogent:{author}:{pid}{payload}"'
    if slot is None:
        raise SignError(
            "no safe signature slot in the final logic statement; "
            "add an unconditional jump with an unused compare slot")
    lines[slot.index] = f"{slot.prefix} {sig}"
    return "\n".join(lines) + "\n", pid


def verify_text(text: str) -> list[str]:
    hits = _find(text)
    if not hits:
        return ['missing hidden @aigenerated argument '
                '(expected `jump <target> always <unused> "AI-Generated:Mlogent:<author>:<body-id>:<payload>"`)']
    if len(hits) > 1:
        return [f"{len(hits)} @aigenerated arguments found, expected 1"]
    author, want = hits[0].group(1), hits[0].group(2)
    try:
        _, _, labels = decode_signature_payload(hits[0].group(3))
    except SignError as exc:
        return [str(exc)]
    got = _hash(author, _body(text), labels)[:12]
    if want != got:
        return [f"body changed after signing (id {want} != {got})"]
    return []


