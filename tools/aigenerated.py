"""Hidden @aigenerated signature for AI-written mlog.

    python tools/aigenerated.py sign   Logic/foo.mlog [--author MAI] [--force]
    python tools/aigenerated.py verify Logic/foo.mlog
    python tools/aigenerated.py strip  Logic/foo.mlog   # always refused

Where the mark lives
--------------------
Preferred: if the program's last real statement is an unconditional
`jump <n> always <x>`, the token replaces its unused `compare` slot (the
fourth and last operand; `always` never reads it):

    jump 27 always 0 "aigenerated:MAI:1f02465d9e75"

A bare `jump <n> always` (no value operand) gets one spelled out as `0` first,
because `always` never reads it either:

    jump 27 always 0 "aigenerated:MAI:1f02465d9e75"

Either way the `end` that used to follow such a jump is dropped: an
unconditional jump never falls through, so that `end` could not run and
`mlogcheck` reports it as an unreachable statement (v0.13.2 rule
`unreachable-statement`).  Signing therefore never adds a statement and never
leaves a dead one behind.

Otherwise the closing `end` becomes

    jump 0 always 0 "aigenerated:MAI:1f02465d9e75"

`end` means "next instruction reads 0"; `jump 0 always` does the same thing, so
the program behaves identically.  The token sits in a declared `JumpStatement`
operand that `always` never reads, so the game's own `LAssembler.read` /
`LAssembler.write` round-trip re-emits it verbatim (measured on v160.7 with the
four-operand form, no `end`: `b.code` comes back byte-identical).  A surplus
token after `end`, `set` or `op` is *not* used: `LogicIO.write` drops everything
past the declared arity (measured on v160.7, see mlog工作笔记).  A program with
no `end` gets one appended by the canonical form, then the same replacement
applies.

Why not a comment?
-----------------
`#` comments are stripped when a blueprint is compiled, and the in-game editor
makes a leading comment obvious.

Removal policy
--------------
There is deliberately no `strip` mode: the signature is an attribution term.
Anyone can edit the text, but `verify` re-hashes the body without the token,
so deleting it or changing the logic both fail.  Re-sign after an intentional
edit with `sign --force`; that produces a new id.

The id is the first 12 hex of SHA-256 over `author + "\\n" + body`, with the
body normalised to LF, the signature line removed, and a trailing `end`
guaranteed (so signing is idempotent even for programs that omitted it).
"""
import argparse
import base64
import hashlib
import json
import os
import re
import sys
import zlib
from pathlib import Path

DEFAULT_AUTHOR = "MAI"
PROJECT_NAME = "Mlogent"
PROJECT_VERSION = os.environ.get("MLOGENT_VERSION", "1.8.0")
PROJECT_REPO = "https://github.com/EnernalIliary/Mlogent"
# the sidecar (tools/logicd.py, tools/jobqueue.py) signs with this one; the
# environment override exists so a build can attribute a different author
SIGN_AUTHOR = os.environ.get("MAI_SIGN_AUTHOR") or DEFAULT_AUTHOR
SIG_LINE = 'jump 0 always 0 "AI-Generated:Mlogent:{author}:{pid}{payload}"'
# addr/value are not captured: author/id/payload stay at groups 1/2/3
SIG_RE = re.compile(
    r'^jump\s+\S+\s+always\s+\S+\s+"AI-Generated:Mlogent:([^":]+):([0-9a-f]{12})'
    r'(?::([A-Za-z0-9_-]+))?"\s*$')
SIG_PARTS_RE = re.compile(r'^jump\s+(\S+)\s+always\s+(\S+)\s+"AI-Generated:Mlogent:')
# older releases used a comment header + unreachable set; drop those on re-sign
OLD_MARK_RE = re.compile(
    r"^(?:# @aigenerated(?:-end)?\b.*|set aigenerated\.[0-9a-f]{12}\b.*)$")
# release 0.9 put the token after `end`; normalise that back to a plain `end`
OLD_TAIL_RE = re.compile(r'^end\s+"AI-Generated:Mlogent:[^"]*"\s*$')


class SignError(Exception):
    pass


def _read(path: Path) -> str:
    return (path.read_text(encoding="utf-8-sig")
            .replace("\r\n", "\n").replace("\r", "\n"))


def _write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


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


LABEL_NAME = re.compile(r"[A-Za-z_][\w.\-]*")
_LABEL_LINE = re.compile(r"^\s*(" + LABEL_NAME.pattern + r"):\s*$")


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
            out.append({"line": no, "stmt": stmt, "text": s})
            continue
        if _LABEL_LINE.match(line):
            continue
        stmt += 1
    return out


PAYLOAD_V = 3

#: meta 里这四把键是有意义的：ws（工作区 id）、name（工作区/蓝图名）、
#: prompt（用户那句话）、job（作业 id）。mod 侧只认这四个，别的一律忽略。
META_KEYS = ("tool", "version", "repo", "author", "ws", "name", "prompt", "job")


def project_meta(author: str) -> dict:
    return {"tool": PROJECT_NAME, "version": PROJECT_VERSION,
            "repo": PROJECT_REPO, "author": author}


def _meta_text(value, limit: int) -> str:
    """meta 是塞进 mlog 字符串字面量里的：引号、反斜杠、换行都会毁掉那一行。"""
    out = []
    for ch in str(value or ""):
        if ch == '"' or ch == "\\":
            out.append("'")
        elif ch in "\r\n\t":
            out.append(" ")
        elif ord(ch) < 32:
            continue
        else:
            out.append(ch)
    return " ".join("".join(out).split())[:limit]


def meta_of_job(job: dict) -> dict | None:
    """作业 -> 跟着代码走的上下文（蓝图「详细」页续聊靠它认人）。"""
    ws = job.get("workspace") if isinstance(job.get("workspace"), dict) else {}
    out = {}
    ws_id = _meta_text(ws.get("id"), 64)
    if ws_id:
        out["ws"] = ws_id
    name = _meta_text(ws.get("name"), 40)
    if name:
        out["name"] = name
    prompt = _meta_text(job.get("desc"), 160)
    if prompt:
        out["prompt"] = prompt
    jid = _meta_text(job.get("id"), 24)
    if jid:
        out["job"] = jid
    return out or None


def encode_comments(comments: list[dict], meta: dict | None = None, *,
                    labels: dict[int, str] | None = None) -> str:
    """Encode comment-only v1 or v2 with optional context and primary labels.

    v2 readers can keep consuming c/m and ignore the optional labels field.
    Labels are sorted pairs of zero-based statement index and name.
    """
    if not comments and not meta and not labels:
        return ""
    rows = [[c["line"], c["stmt"], c["text"]] for c in comments]
    obj = {"v": PAYLOAD_V, "c": rows, "m": meta} if meta or labels else rows
    if labels:
        obj["labels"] = sorted(labels.items())
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    comp = zlib.compress(raw, 9)
    blob = (b"z" + comp) if len(comp) < len(raw) else (b"j" + raw)
    return base64.urlsafe_b64encode(blob).decode("ascii").rstrip("=")


def decode_signature_payload(payload: str | None) -> tuple[list[dict], dict | None, dict[int, str]]:
    """Read comments, context and the optional v2 primary label table."""
    if not payload:
        return [], None, {}
    pad = "=" * (-len(payload) % 4)
    try:
        blob = base64.urlsafe_b64decode(payload + pad)
        raw = zlib.decompress(blob[1:]) if blob[:1] == b"z" else blob[1:]
        doc = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, zlib.error, json.JSONDecodeError):
        raise SignError("bad comment payload in the signature")
    meta = None
    labels = {}
    rows = doc
    if isinstance(doc, dict):
        rows = doc.get("c") or []
        m = doc.get("m")
        if isinstance(m, dict):
            meta = {k: str(m[k])[:200] for k in META_KEYS if str(m.get(k) or "")}
            meta = meta or None
        if "labels" in doc:
            label_rows = doc["labels"]
            if not isinstance(label_rows, list) or not label_rows:
                raise SignError("bad label table in the signature")
            names = set()
            for row in label_rows:
                if not isinstance(row, list) or len(row) != 2:
                    raise SignError("bad label table in the signature")
                target, name = row
                if (type(target) is not int or target < 0 or target in labels
                        or not isinstance(name, str) or not LABEL_NAME.fullmatch(name)
                        or name in names):
                    raise SignError("bad label table in the signature")
                labels[target] = name
                names.add(name)
    if not isinstance(rows, list):
        raise SignError("bad comment payload in the signature")
    try:
        comments = [{"line": int(r[0]), "stmt": int(r[1]), "text": str(r[2])} for r in rows]
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise SignError("bad comment payload in the signature") from exc
    return comments, meta, labels


def decode_payload(payload: str | None) -> tuple[list[dict], dict | None]:
    comments, meta, _ = decode_signature_payload(payload)
    return comments, meta


def decode_comments(payload: str | None) -> list[dict]:
    return decode_payload(payload)[0]


def decode_meta(payload: str | None) -> dict | None:
    return decode_payload(payload)[1]


def _hash(author: str, body: str, labels: dict[int, str] | None = None) -> str:
    material = author + "\n" + body
    if labels:
        material += "\0labels\0" + json.dumps(sorted(labels.items()), separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _find(text: str):
    text = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    return [m for m in (SIG_RE.match(ln.strip()) for ln in text.split("\n")) if m]


def sign_text(text: str, author: str = DEFAULT_AUTHOR, force: bool = False,
              comments: list[dict] | None = None, meta: dict | None = None,
              *, labels: dict[int, str] | None = None):
    """Return (signed_text, id).  Raises SignError if it would change an id.

    Comments are moved into the signature string (base64 payload), so the
    delivered code carries them without occupying lines: no `#` line survives in
    the signed text (the game's assembler drops them, and `b.code` is rebuilt from
    the assembled program, so a kept one would look like a write that never
    landed).  The id still hashes the canonical body, comments included.
    """
    hits = _find(text)
    body = _body(text)
    # an already-signed program whose body is nothing but the signature is fine to
    # re-sign (its canonical body is ""); only a text with nothing in it at all is
    # refused, because there would be no statement to attach the token to
    if not body and not hits:
        raise SignError("no statement to attach the signature to")
    author = re.sub(r'[:"]', "", author).strip() or DEFAULT_AUTHOR
    # the body always ends with `end`; when the statement just before it is an
    # unconditional jump the token goes into that jump's value slot instead, and
    # the `end` behind it is dropped (see the comment further down).  The id has
    # to hash the body `verify_text` will rebuild from the signed text, so a
    # `jump <n> always` tail is spelled out as `jump <n> always 0` first.
    lines = body.rstrip("\n").split("\n") if body else [""]
    # comments travel in the signature payload, never as lines of the delivered
    # code: the game's assembler drops `#` lines, and `b.code` -- which the mod
    # compares with the job's code character by character -- is rebuilt from the
    # assembled program, so a kept comment line would read as "the write did not
    # land". The id covers the code body and, when present, the label table.
    lines = [l for l in lines if not l.strip().startswith("#")]
    idx = len(lines) - 1
    slot = None
    while idx >= 0:
        m = re.match(r'^(jump\s+(\S+)\s+always)\s+(\S+)\s*$', lines[idx].strip())
        if m:
            slot = f"{m.group(1)} {m.group(3)}"
            break
        elif m is None:
            m = re.match(r'^(jump\s+(\S+)\s+always)\s*$', lines[idx].strip())
            if m:
                slot = f"{m.group(1)} 0"
                lines[idx] = slot
                body = "\n".join(lines) + "\n"
                break
        idx -= 1
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
    lines[idx] = f"{slot} {sig}"
    return "\n".join(lines) + "\n", pid


def verify_text(text: str) -> list[str]:
    hits = _find(text)
    if not hits:
        return ['missing hidden @aigenerated argument '
                '(expected `jump 0 always 0 "aigenerated:<author>:<id>"`)']
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


def sign(path: Path, author: str, force: bool) -> str:
    text = _read(path)
    if not _body(text):
        raise SignError(f"{path}: no statement to attach the signature to")
    try:
        signed, pid = sign_text(text, author, force=force)
    except SignError as exc:
        raise SignError(f"{path}: {exc}") from exc
    if signed == text and not force:
        return f"already signed  {path}  id={pid}"
    _write(path, signed)
    return f"signed  {path}  id={pid}  author={author}"


def verify(path: Path) -> list[str]:
    return [f"{path}: {p}" for p in verify_text(_read(path))]


LABEL_LINE_RE = _LABEL_LINE
JUMP_LABEL_RE = re.compile(r"^(\s*jump\s+)([A-Za-z_][\w.\-]*)(\s+.*)?$", re.I)


def _resolve_labels(text: str, *, strict: bool = False) -> tuple[str, dict[str, int], int]:
    """Turn `jump label` back into `jump N` and drop the label lines.

    A label line does not occupy a statement slot, so `label -> N` is the
    number of statements before it. Unknown labels are left untouched.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    labels: dict[str, int] = {}
    kinds: list[str] = []
    idx = 0
    for line in lines:
        s = line.strip()
        m = LABEL_LINE_RE.match(line)
        if not s or s.startswith("#"):
            kinds.append("keep")
        elif m:
            name = m.group(1)
            if strict and name in labels:
                raise SignError(f"duplicate label {name!r}")
            labels[name] = idx
            kinds.append("label")
        else:
            kinds.append("stmt")
            idx += 1
    out: list[str] = []
    rewritten = 0
    for line, kind in zip(lines, kinds):
        if kind == "label":
            continue
        if kind == "stmt":
            m = JUMP_LABEL_RE.match(line)
            if m and not m.group(2).isdigit() and m.group(2) in labels:
                line = f"{m.group(1)}{labels[m.group(2)]}{m.group(3) or ''}"
                rewritten += 1
        out.append(line)
    return "\n".join(out) + "\n", labels, rewritten


def resolve_labels(text: str) -> tuple[str, int, int]:
    numeric, labels, rewritten = _resolve_labels(text)
    return numeric, len(labels), rewritten


def _group_comments(text: str) -> str:
    """Move every `#` line to just before the signature (delivery layout)."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    code, comments = [], []
    for line in lines:
        if line.strip().startswith("#"):
            comments.append(line.rstrip())
        elif line.strip() or code:
            code.append(line.rstrip())
    while code and not code[-1].strip():
        code.pop()
    if not comments:
        return "\n".join(code) + "\n"
    return "\n".join(code + [""] + comments) + "\n"


def sign_delivery(text: str, author: str) -> tuple[str, str, int, int]:
    """Resolve editable labels and carry the first name per target in the payload."""
    hits = _find(text)
    comments = meta = None
    saved_labels = {}
    if hits:
        if not verify_text(text):
            author = hits[0].group(1)
            comments, meta, saved_labels = decode_signature_payload(hits[0].group(3))
        # Strip the old token before resolving jumps: converting a label in a
        # signature-bearing tail jump to 0 can otherwise hide that instruction.
        if comments is None:
            comments = collect_comments(text)
        text = _body(text)

    numeric, declarations, rewritten = _resolve_labels(text, strict=True)
    canonical = _body(numeric)
    count = sum(bool(line.strip()) for line in canonical.splitlines())
    labels: dict[int, str] = {}
    for name, target in declarations.items():
        if target < count:
            labels.setdefault(target, name)
    if not declarations:
        labels = {target: name for target, name in saved_labels.items() if target < count}
    if comments is None:
        comments = collect_comments(text)
    signed, pid = sign_text(numeric, author, force=True, comments=comments, meta=meta, labels=labels)
    return signed, pid, len(declarations), rewritten


def post(path: Path, author: str, output: Path | None = None) -> str:
    """Delivery post-process: labels -> line numbers, then sign."""
    signed, pid, nlabels, rewritten = sign_delivery(_read(path), author)
    if has_saved_labels(signed):
        from msch import build_logic_data, check_logic_config_limits
        try:
            check_logic_config_limits(signed, build_logic_data(signed, []))
        except ValueError as exc:
            raise SignError(str(exc)) from exc
    dst = output or path
    _write(dst, signed)
    author = _find(signed)[0].group(1)
    return (f"post  {dst}: {nlabels} label(s), {rewritten} jump(s) numeric; "
            f"signed id={pid} author={author}")


def has_saved_labels(text: str) -> bool:
    hits = _find(text)
    return bool(hits and decode_signature_payload(hits[0].group(3))[2])


def extract_text(text: str) -> list[dict]:
    hits = _find(text)
    if not hits:
        raise SignError("missing hidden @aigenerated argument")
    return decode_comments(hits[0].group(3))


def restore_text(text: str) -> tuple[str, str, list[dict]]:
    """Put the comments back before their anchor statements, same token."""
    hits = _find(text)
    if not hits:
        raise SignError("missing hidden @aigenerated argument")
    author = hits[0].group(1)
    cs = decode_comments(hits[0].group(3))
    body = _body(text)
    lines = body.rstrip("\n").split("\n")
    total = len(lines)
    buckets: dict[int, list[dict]] = {}
    for c in cs:
        buckets.setdefault(min(max(c["stmt"], 0), total), []).append(c)
    out: list[str] = []
    for i, line in enumerate(lines):
        out.extend(c["text"] for c in buckets.pop(i, []))
        if line.strip() == "end" and i == total - 1:
            out.extend(c["text"] for k in sorted(buckets) for c in buckets[k])
            buckets.clear()
        out.append(line)
    out.extend(c["text"] for k in sorted(buckets) for c in buckets[k])
    # Preserve the complete token payload, including the label table.
    enc = hits[0].group(3)
    payload = f":{enc}" if enc else ""
    sig = SIG_LINE.format(author=author, pid=hits[0].group(2), payload=payload)
    while out and not out[-1].strip():
        out.pop()
    out[-1] = sig
    return "\n".join(out) + "\n", hits[0].group(2), cs


def main(argv) -> int:
    # 控制台编码可能是 cp1252 之类（Windows 非中文区、CI 默认），签名里带作者中文就会炸；
    # 输出只是给人看的，切到 UTF-8 并容错替换即可，文件读写本来都是显式 UTF-8。
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="hidden @aigenerated signature for AI-written mlog")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("sign", help="add/replace the hidden argument")
    ps.add_argument("files", nargs="+")
    ps.add_argument("--author", default=DEFAULT_AUTHOR)
    ps.add_argument("--force", action="store_true", help="re-sign after an intentional edit")

    pv = sub.add_parser("verify", help="check the hidden argument and body hash")
    pv.add_argument("files", nargs="+")

    pt = sub.add_parser("strip", help="refused by policy")
    pt.add_argument("files", nargs="+")

    pp = sub.add_parser("post", help="delivery post-process: labels -> numbers, then sign")
    pp.add_argument("files", nargs="+")
    pp.add_argument("--author", default=DEFAULT_AUTHOR)
    pp.add_argument("-o", "--output", help="write here instead of in place (single file)")

    pe = sub.add_parser("extract", help="list the comments hidden in the signature")
    pe.add_argument("files", nargs="+")

    pr = sub.add_parser("restore", help="put the hidden comments back into the file")
    pr.add_argument("files", nargs="+")

    args = ap.parse_args(argv)
    if args.cmd == "strip":
        print("refused: the @aigenerated signature is an attribution term and cannot be stripped;\n"
              "edit the logic and re-sign with `sign --force` instead", file=sys.stderr)
        return 2

    failed = 0
    for name in args.files:
        path = Path(name)
        if not path.is_file():
            print(f"missing file: {path}", file=sys.stderr)
            failed += 1
            continue
        if args.cmd == "extract":
            try:
                for c in extract_text(_read(path)):
                    print(f"L{c['line']} (stmt {c['stmt']}): {c['text']}")
            except SignError as e:
                print(f"FAIL  {path}: {e}", file=sys.stderr)
                failed += 1
        elif args.cmd == "restore":
            try:
                signed, pid, cs = restore_text(_read(path))
                _write(path, signed)
                print(f"restored  {path}: {len(cs)} comment(s), id={pid}")
            except SignError as e:
                print(f"FAIL  {path}: {e}", file=sys.stderr)
                failed += 1
        elif args.cmd == "post":
            if args.output and len(args.files) != 1:
                print("-o/--output only works with a single file", file=sys.stderr)
                return 2
            try:
                print(post(path, args.author, Path(args.output) if args.output else None))
            except SignError as e:
                print(f"FAIL  {e}", file=sys.stderr)
                failed += 1
        elif args.cmd == "sign":
            try:
                print(sign(path, args.author, args.force))
            except SignError as e:
                print(f"FAIL  {e}", file=sys.stderr)
                failed += 1
        else:
            problems = verify(path)
            if problems:
                failed += 1
                for p in problems:
                    print("FAIL  " + p, file=sys.stderr)
            else:
                m = _find(_read(path))[0]
                print(f"OK    {path}  id={m.group(2)}  author={m.group(1)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
