"""Minimal OAuth 2.1 authorization server for the mlog MCP endpoint.

Just enough of RFC 8414 / RFC 9728 / RFC 7591 / RFC 7636 for MCP clients:
protected-resource metadata, authorization-server metadata, dynamic client
registration, authorization code + PKCE (S256) behind a password consent page,
and refresh tokens.  Access tokens are opaque and stored in a JSON file next to
the service config; the static MLOG_MCP_TOKEN keeps working alongside them.
"""
import base64
import hashlib
import html
import json
import mlog_acl as ACL
import os
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import parse_qs, urlencode, urlsplit

BASE = os.environ.get("MLOG_OAUTH_BASE", "https://mcp.iliary.life").rstrip("/")
ROOT = Path(__file__).resolve().parent.parent
STORE = os.environ.get("MLOG_OAUTH_STORE", str(ROOT / "out" / "oauth_state.json"))
PASSWORD = os.environ.get("MLOG_OAUTH_PASSWORD", "")
ENABLED = bool(PASSWORD)

CODE_TTL = 600
ACCESS_TTL = 3600
REFRESH_TTL = 30 * 86400

_LOCK = threading.Lock()


def _empty():
    return {"clients": {}, "codes": {}, "tokens": {}, "refresh": {}}


def _is_live(entry):
    if not isinstance(entry, dict):
        return False
    try:
        return float(entry.get("exp") or 0) > time.time()
    except (TypeError, ValueError):
        return False


def _load_unlocked():
    try:
        with open(STORE, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return _empty()
    if not isinstance(data, dict):
        return _empty()
    for key in ("clients", "codes", "tokens", "refresh"):
        if not isinstance(data.get(key), dict):
            data[key] = {}
    return data


def _load():
    with _LOCK:
        return _load_unlocked()


def _write_unlocked(data):
    for bucket in ("codes", "tokens", "refresh"):
        table = data.get(bucket) or {}
        for token, entry in list(table.items()):
            if not _is_live(entry):
                table.pop(token, None)
    tmp = STORE + ".tmp"
    os.makedirs(os.path.dirname(STORE) or ".", exist_ok=True)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.replace(tmp, STORE)
        os.chmod(STORE, 0o600)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def _save(data):
    with _LOCK:
        _write_unlocked(data)


def _json(status, obj, extra=None):
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    headers = {"Cache-Control": "no-store"}
    headers.update(extra or {})
    return status, "application/json; charset=utf-8", body, headers


def _text(status, body, ctype="text/plain; charset=utf-8", extra=None):
    return status, ctype, body.encode("utf-8"), dict(extra or {})


def resource_metadata():
    return {
        "resource": BASE,
        "authorization_servers": [BASE],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["mcp"],
    }


def as_metadata():
    return {
        "issuer": BASE,
        "authorization_endpoint": BASE + "/authorize",
        "token_endpoint": BASE + "/token",
        "registration_endpoint": BASE + "/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["mcp"],
        "service_documentation": BASE + "/health",
    }


def resolve(token):
    """The live token record (client_id, scope, profile, user) or None."""
    if not ENABLED or not token:
        return None
    entry = (_load().get("tokens") or {}).get(token)
    if _is_live(entry):
        return entry
    return None


def check_access(token):
    """True when TOKEN is a live OAuth access token."""
    return resolve(token) is not None


def never_challenge():
    return 'Bearer realm="mlog-mcp", resource_metadata="%s/.well-known/oauth-protected-resource"' % BASE


def _pkce_ok(verifier, challenge):
    if not verifier or not challenge:
        return False
    try:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
    except UnicodeEncodeError:
        return False
    calc = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return secrets.compare_digest(calc, challenge)


def _valid_redirect_uri(uri):
    if not isinstance(uri, str) or not uri or any(ord(char) < 0x20 for char in uri):
        return False
    try:
        parsed = urlsplit(uri)
        scheme = parsed.scheme.lower()
        hostname = (parsed.hostname or "").lower()
    except ValueError:
        return False
    if not scheme or parsed.fragment or parsed.username or parsed.password:
        return False
    if scheme in {"http", "https"}:
        if not hostname:
            return False
        return scheme == "https" or hostname in {"localhost", "127.0.0.1", "::1"}
    return bool(re.fullmatch(r"[a-z][a-z0-9+.-]*", scheme)) and scheme not in {
        "data", "file", "javascript",
    }


def _register(body):
    try:
        spec = json.loads(body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return _json(400, {"error": "invalid_client_metadata"})
    if not isinstance(spec, dict):
        return _json(400, {"error": "invalid_client_metadata"})
    uris = spec.get("redirect_uris")
    if not isinstance(uris, list) or not uris or not all(_valid_redirect_uri(uri) for uri in uris):
        return _json(400, {"error": "invalid_redirect_uri",
                           "error_description": "redirect_uris must contain valid redirect URIs"})
    client_id = "mlog-" + secrets.token_hex(12)
    client = {
        "client_id": client_id,
        "client_name": str(spec.get("client_name") or "")[:160],
        "redirect_uris": uris,
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "issued_at": int(time.time()),
    }
    with _LOCK:
        data = _load_unlocked()
        data["clients"][client_id] = client
        _write_unlocked(data)
    return _json(201, client)


def _page(message, fields, status=200):
    inputs = "".join(
        '<input type="hidden" name="%s" value="%s">' % (html.escape(k), html.escape(v or ""))
        for k, v in fields.items())
    body = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>授权 · mlog MCP</title>
<style>body{font:15px/1.6 system-ui,sans-serif;max-width:420px;margin:12vh auto;padding:0 20px}
input[type=password]{width:100%%;padding:10px;font-size:15px;margin:8px 0 16px;box-sizing:border-box}
button{padding:10px 18px;font-size:15px;cursor:pointer}
p.err{color:#b00}.muted{color:#666;font-size:13px}</style>
<h2>mlog MCP 授权</h2>
<p>客户端 <b>%s</b> 请求访问 mlog MCP 工具。</p>
<p class="muted">%s</p>
<form method="post" action="/authorize">%s
<label>授权密码<input type="password" name="password" autofocus required></label>
<button type="submit">同意并继续</button></form>
<p class="err">%s</p></html>""" % (
        html.escape(fields.get("client_name") or fields.get("client_id") or "unknown"),
        html.escape(fields.get("redirect_uri") or ""), inputs, html.escape(message or ""))
    return _text(status, body, "text/html; charset=utf-8")


def _authorize_get(query):
    data = _load()
    client_id = query.get("client_id") or ""
    client = data["clients"].get(client_id)
    if not client:
        return _text(400, "unknown client_id")
    redirect_uri = query.get("redirect_uri") or ""
    if redirect_uri not in client["redirect_uris"]:
        return _text(400, "redirect_uri is not registered for this client")
    if (query.get("response_type") or "code") != "code":
        return _text(400, "unsupported response_type")
    if query.get("code_challenge_method") != "S256" or not query.get("code_challenge"):
        return _text(400, "PKCE with S256 is required")
    fields = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": query.get("state") or "",
        "code_challenge": query.get("code_challenge") or "",
        "code_challenge_method": "S256",
        "scope": query.get("scope") or "mcp",
        "client_name": client.get("client_name") or "",
    }
    return _page("", fields)


def _authorize_post(body):
    form = {k: v[0] for k, v in parse_qs(body.decode("utf-8", "replace")).items()}
    data = _load()
    client = data["clients"].get(form.get("client_id") or "")
    if not client:
        return _text(400, "unknown client_id")
    if (form.get("redirect_uri") or "") not in client["redirect_uris"]:
        return _text(400, "redirect_uri is not registered for this client")
    if form.get("code_challenge_method") != "S256" or not form.get("code_challenge"):
        return _text(400, "PKCE with S256 is required")
    form["client_name"] = client.get("client_name") or ""
    who = ACL.match_password(form.get("password") or "")
    if who is None:
        return _page("密码不对。", form, status=401)
    code = secrets.token_urlsafe(32)
    with _LOCK:
        data = _load_unlocked()
        client = data["clients"].get(form["client_id"])
        if not client or form["redirect_uri"] not in client["redirect_uris"]:
            return _text(400, "unknown client_id or redirect_uri")
        data["codes"][code] = {
            "client_id": form["client_id"],
            "redirect_uri": form["redirect_uri"],
            "code_challenge": form["code_challenge"],
            "scope": form.get("scope") or "mcp",
            "profile": who["profile"],
            "user": who["name"],
            "exp": time.time() + CODE_TTL,
        }
        _write_unlocked(data)
    params = {"code": code}
    if form.get("state"):
        params["state"] = form["state"]
    location = form["redirect_uri"] + ("&" if "?" in form["redirect_uri"] else "?") + urlencode(params)
    return _text(302, "", extra={"Location": location})


def _issue(data, client_id, scope, profile="runner", user=""):
    access = "mlog_at_" + secrets.token_urlsafe(32)
    refresh = "mlog_rt_" + secrets.token_urlsafe(32)
    data["tokens"][access] = {"client_id": client_id, "scope": scope, "profile": profile,
                              "user": user, "exp": time.time() + ACCESS_TTL}
    data["refresh"][refresh] = {"client_id": client_id, "scope": scope, "profile": profile,
                                "user": user, "exp": time.time() + REFRESH_TTL}
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": ACCESS_TTL,
        "refresh_token": refresh,
        "scope": scope,
    }


def _token(body):
    form = {k: v[0] for k, v in parse_qs(body.decode("utf-8", "replace")).items()}
    grant = form.get("grant_type") or ""
    if grant not in {"authorization_code", "refresh_token"}:
        return _json(400, {"error": "unsupported_grant_type"})
    with _LOCK:
        data = _load_unlocked()
        if grant == "authorization_code":
            code = form.get("code") or ""
            entry = data["codes"].get(code)
            if not _is_live(entry):
                return _json(400, {"error": "invalid_grant"})
            if entry.get("client_id") != form.get("client_id"):
                return _json(400, {"error": "invalid_grant"})
            if form.get("redirect_uri") != entry.get("redirect_uri"):
                return _json(400, {"error": "invalid_grant"})
            data["codes"].pop(code, None)
            if not _pkce_ok(form.get("code_verifier") or "", entry.get("code_challenge")):
                _write_unlocked(data)
                return _json(400, {"error": "invalid_grant", "error_description": "PKCE check failed"})
            payload = _issue(data, entry["client_id"], entry.get("scope") or "mcp",
                             entry.get("profile") or "runner", entry.get("user") or "")
            _write_unlocked(data)
            return _json(200, payload)

        refresh = form.get("refresh_token") or ""
        entry = data["refresh"].get(refresh)
        if not _is_live(entry):
            return _json(400, {"error": "invalid_grant"})
        if form.get("client_id") and entry.get("client_id") != form["client_id"]:
            return _json(400, {"error": "invalid_grant"})
        data["refresh"].pop(refresh, None)
        payload = _issue(data, entry["client_id"], entry.get("scope") or "mcp",
                         entry.get("profile") or "runner", entry.get("user") or "")
        _write_unlocked(data)
        return _json(200, payload)


def route(method, path, query, headers, body):
    """Answer an OAuth request, or return None when the path is not ours."""
    if not ENABLED:
        return None
    if path.rstrip("/") == "/.well-known/oauth-protected-resource":
        return _json(200, resource_metadata())
    if path.rstrip("/") == "/.well-known/oauth-authorization-server":
        return _json(200, as_metadata())
    if path == "/register" and method == "POST":
        return _register(body)
    if path == "/authorize":
        if method == "GET":
            return _authorize_get(query)
        if method == "POST":
            return _authorize_post(body)
        return _text(405, "method not allowed", extra={"Allow": "GET, POST"})
    if path == "/token" and method == "POST":
        return _token(body)
    return None
