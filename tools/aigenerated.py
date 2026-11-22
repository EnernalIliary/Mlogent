"""Hidden Mlogent signature for AI-written mlog.

    python tools/aigenerated.py sign   Logic/foo.mlog [--author MAI] [--force]
    python tools/aigenerated.py verify Logic/foo.mlog
    python tools/aigenerated.py strip  Logic/foo.mlog   # always refused

Where the mark lives
--------------------
The token is mounted only in an existing unconditional `jump <n> always <x>`
statement's unused `compare` slot (the fourth and last operand; `always` never
reads it):

    jump 27 always 0 "AI-Generated:Mlogent:MAI:<body-id>:<payload>"

A bare `jump <n> always` (no value operand) gets one spelled out as `0` first,
because `always` never reads it either:

    jump 27 always 0 "AI-Generated:Mlogent:MAI:<body-id>:<payload>"

The existing statements, including `end`, are preserved. Editable labelized
output restores the token as a trailing comment; delivery post-processing
moves it back into the safe slot. If no safe slot is available signing fails;
callers that explicitly permit unsigned output may write without a signature.

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
body normalised to LF, the signature operand/comment removed, and a trailing `end`
guaranteed (so signing is idempotent even for programs that omitted it).
"""
import argparse
import sys
from pathlib import Path

from mlogent.logic.labels import LABEL_NAME_RE as LABEL_NAME, LABEL_RE as _LABEL_LINE
from mlogent.logic.labels import JUMP_LABEL_RE, LabelError, resolve as _resolve_label_source

from mlogent.logic.signature import (
    DEFAULT_AUTHOR, PROJECT_NAME, PROJECT_VERSION, PROJECT_REPO, SIGN_AUTHOR,
    SIG_LINE, SIG_RE, SIG_COMMENT_RE, SIG_PARTS_RE, OLD_MARK_RE, OLD_TAIL_RE,
    SignError, PAYLOAD_V, META_KEYS, project_meta, _meta_text, meta_of_job,
    encode_comments, decode_signature_payload, decode_payload, decode_comments, decode_meta,
    _clean, _canonical, _body, collect_comments, _hash, _find, sign_text, verify_text,
)


def _read(path: Path) -> str:
    return (path.read_text(encoding="utf-8-sig")
            .replace("\r\n", "\n").replace("\r", "\n"))


def _write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


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


def _resolve_labels(text: str, *, strict: bool = False) -> tuple[str, dict[str, int], int]:
    """Compatibility wrapper preserving signature-specific error handling."""
    try:
        return _resolve_label_source(text, strict=strict)
    except LabelError as exc:
        raise SignError(str(exc)) from exc


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
    """Compatibility entry point for the shared delivery-source conversion."""
    from mlogent.logic.source import to_delivery

    return to_delivery(text, author)


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
    """Restore comment anchors and expose the token in editable source."""
    from mlogent.logic.source import restore_comments

    return restore_comments(text)


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
    # Shared conversion code imports this module by name. Keep one SignError
    # class when invoked as a script so CLI errors still use the normal handler.
    sys.modules.setdefault("aigenerated", sys.modules[__name__])
    raise SystemExit(main(sys.argv[1:]))
