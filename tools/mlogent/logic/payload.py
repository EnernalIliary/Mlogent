"""Signature payload codec; preserves the existing wire format and bytes."""
import base64
import json
import zlib

from .labels import LABEL_NAME_RE as LABEL_NAME


class SignError(Exception):
    """Signature input, payload or safe-slot validation failed."""


PAYLOAD_V = 3

#: meta 里这四把键是有意义的：ws（工作区 id）、name（工作区/蓝图名）、
#: prompt（用户那句话）、job（作业 id）。mod 侧只认这四个，别的一律忽略。
META_KEYS = ("tool", "version", "repo", "author", "ws", "name", "prompt", "job")


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
    """Encode comments, optional context and primary labels.

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
    """Read comments, context and the optional primary label table."""
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


