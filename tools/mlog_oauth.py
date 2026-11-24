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
import mlog_github_login as GITHUB
import mlog_google_login as GOOGLE
import mlog_auth_i18n as AUTH_LANG
import sys
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
    language = AUTH_LANG.choose(fields.get("ui_lang"))
    # Only protocol fields return to the form; never echo a submitted password.
    keys = ("client_id", "redirect_uri", "state", "code_challenge",
            "code_challenge_method", "scope", "client_name", "login_ticket", "ui_lang")
    inputs = "".join(
        '<input type="hidden" name="%s" value="%s">' %
        (html.escape(key, quote=True), html.escape(str(fields.get(key) or ""), quote=True))
        for key in keys if key in fields)
    values = {
        "CLIENT": html.escape(str(fields.get("client_name") or fields.get("client_id") or "?????")),
        "REDIRECT": html.escape(str(fields.get("redirect_uri") or "")),
        "SCOPE": html.escape(str(fields.get("scope") or "mcp")),
        "INPUTS": inputs,
        "ERROR": html.escape(AUTH_LANG.tr(str(message or ""), language)),
    }
    template = '<!doctype html>\n<html lang="zh-CN">\n<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="referrer" content="no-referrer"><meta name="color-scheme" content="light"><link rel="icon" type="image/png" sizes="32x32" href="/assets/mlogent/mlogent-icon.png?v=world-processor-1"><title>连接授权 · Mlogent MCP</title>\n<style>\n:root{font-family:system-ui,\'Microsoft YaHei\',sans-serif;color:#252c27;background:#f5f3eb;--line:#d9d9cd;--muted:#74776b;--orange:#c4582f;--mono:Consolas,monospace}*{box-sizing:border-box}body{margin:0}a{color:inherit;text-decoration:none}a:focus-visible,button:focus-visible{outline:2px solid var(--orange);outline-offset:5px}.header{max-width:1120px;margin:auto;padding:27px 32px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line)}.brand{font-size:22px;font-weight:800;letter-spacing:-.8px}.brand span{color:var(--orange);font-family:var(--mono);margin-right:9px}.header>a:last-child{font-size:12px;color:var(--muted)}main{max-width:1000px;margin:68px auto 60px;padding:0 32px;display:grid;grid-template-columns:1fr 1.12fr;gap:72px;align-items:start}.eyebrow{font:10px var(--mono);letter-spacing:1.5px;color:#5e704e;margin:0 0 25px}.eyebrow:before{content:\'\';display:inline-block;width:6px;height:6px;background:var(--orange);border-radius:50%;margin-right:9px}h1{font-size:42px;line-height:1.4;letter-spacing:-1.5px;margin:0 0 23px;font-weight:750}h1 span{color:var(--orange)}.intro{font-size:14px;line-height:1.95;color:#6b7063}.connection{margin-top:37px;padding:22px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center;font:11px var(--mono)}.app-icon{width:37px;height:37px;display:flex;align-items:center;justify-content:center;border:1px solid #aab69a;color:#5e704e;background:#e9eddf;font-size:19px}.connection small{display:block;color:var(--muted);font-size:9px;letter-spacing:1px;margin-bottom:5px}.connection strong{font-size:12px;overflow-wrap:anywhere}.connection .arrow{color:var(--orange);font-size:22px;margin:0 auto}.protocol{font:9px/1.8 var(--mono);letter-spacing:1px;color:var(--muted);margin-top:18px}.card{background:#fffef8;border:1px solid #d4d7c8;padding:29px 30px;box-shadow:7px 7px 0 #e8e7dc}.card-top{display:flex;justify-content:space-between;align-items:center;padding-bottom:20px;border-bottom:1px solid var(--line);font:9px var(--mono);letter-spacing:1.2px;color:var(--muted)}.card-top b{color:#5e704e;font-weight:400}.card h2{font-size:21px;margin:24px 0 13px}.request{font-size:13px;line-height:1.85;color:#69705e;margin:0 0 21px}.request strong{color:#252c27;overflow-wrap:anywhere}.details{background:#eff0e7;border:1px solid #dde0d2;margin-bottom:23px;padding:15px}.details dt{font:9px var(--mono);color:#6a755e;letter-spacing:1px;margin-bottom:7px}.details dd{margin:0;font:11px/1.8 var(--mono);overflow-wrap:anywhere;color:#535d49}.details dt:not(:first-child){margin-top:13px}label{display:block;font-size:12px;font-weight:600;margin-bottom:9px}input[type=password]{width:100%;padding:14px;border:1px solid #b9c1ab;background:#fffef8;font-size:15px;box-sizing:border-box;border-radius:0;color:#252c27}input[type=password]:focus{outline:2px solid #70835b;outline-offset:2px}.field-help{font-size:11px;color:var(--muted);line-height:1.85;margin:10px 0 0}.error{color:#a73526;background:#fff0e9;border-left:3px solid #b64d32;font-size:12px;line-height:1.8;padding:11px 13px;margin:17px 0}.error:empty{display:none}button{width:100%;display:flex;align-items:center;justify-content:space-between;background:#252c27;color:#f5f3eb;padding:15px 17px;font:600 13px system-ui,sans-serif;border:0;cursor:pointer;margin-top:21px}button:hover{background:#c4582f}button>span{font-size:21px;font-weight:400}.cancel{display:block;text-align:center;font-size:12px;color:#74776b;padding:17px 0 0}.cancel:hover{color:#c4582f}.consent-note{border-top:1px solid var(--line);padding-top:17px;font-size:11px;line-height:1.9;color:var(--muted);margin:21px 0 0}.privacy{margin-top:30px;display:grid;grid-template-columns:20px 1fr;gap:10px;font-size:11px;color:var(--muted);line-height:1.9}.privacy>span{color:#5e704e;font-size:16px}.privacy p{margin:0}footer{max-width:1056px;margin:auto;padding:24px 32px;border-top:1px solid var(--line);display:flex;justify-content:space-between;color:var(--muted);font:9px/1.8 var(--mono);letter-spacing:.7px}@media(max-width:720px){.header{padding:22px 22px}main{grid-template-columns:1fr;margin:36px auto;padding:0 22px;gap:29px;max-width:540px}h1{font-size:35px;margin-bottom:16px}.intro{font-size:13px}.connection{margin-top:24px}.protocol{margin-bottom:0}.card{padding:24px 22px;box-shadow:5px 5px 0 #e8e7dc}.privacy{margin-top:24px}footer{padding:20px 22px;gap:20px;font-size:8px}.eyebrow{margin-bottom:18px}}\n.brand{display:inline-flex;align-items:center;gap:10px}.brand-icon{image-rendering:pixelated;object-fit:contain;flex:none}\n</style></head>\n<body><header class="header"><a class="brand" href="/"><img class="brand-icon" src="/assets/mlogent/mlogent-icon.png?v=world-processor-1" width="34" height="34" alt="">Mlogent</a><a href="/">了解 Mlogent ↗</a></header>\n<main><section><p class="eyebrow">AUTHORIZE YOUR CONNECTION</p><h1>把工具，<br>交给<span>你的助手。</span></h1><p class="intro">你正在连接 Mlogent MCP。<br>确认请求来自你正在使用的客户端，<br>然后输入已有的授权口令继续。</p><div class="connection"><div class="app-icon">⌘</div><div><small>CLIENT</small><strong>@@CLIENT@@</strong></div><span class="arrow">→</span><div><small>TOOLCHAIN</small><strong>Mlogent MCP</strong></div></div><p class="protocol">OAUTH 2.1 / PKCE S256<br>面向 Mindustry 的逻辑与蓝图工具链</p><div class="privacy"><span>↳</span><p>可使用的工具由账号权限决定。连接成功后，你的客户端将返回对话或配置界面。</p></div></section>\n<section class="card" aria-labelledby="consent-title"><div class="card-top"><span>CONNECTION REQUEST</span><b>01 / AUTHORIZE</b></div><h2 id="consent-title">确认这次连接</h2><p class="request"><strong>@@CLIENT@@</strong> 请求访问 Mlogent MCP。请核对下方回调地址是否属于你的客户端。</p><dl class="details"><dt>RETURN TO / 回调地址</dt><dd>@@REDIRECT@@</dd><dt>REQUESTED SCOPE / 请求范围</dt><dd>@@SCOPE@@</dd></dl>\n<form method="post" action="/authorize" autocomplete="off">@@INPUTS@@<label for="password">授权口令</label><input id="password" type="password" name="password" placeholder="输入你的授权口令" autocomplete="current-password" aria-describedby="password-help auth-error" required autofocus><p class="field-help" id="password-help">使用你已有的授权口令，或向服务管理员获取。此处不是设置新密码。</p><p class="error" id="auth-error" role="alert">@@ERROR@@</p><button type="submit">授权并连接<span aria-hidden="true">↗</span></button></form><a class="cancel" href="/">暂不连接，返回首页</a><p class="consent-note">继续后，客户端将按你账号的现有权限访问工具。若不是你发起的连接，请关闭此页。</p></section></main><footer><span>MLOGENT / MCP CONNECTION</span><span>ILIARY.LIFE · LOGIC, WITH A FEEDBACK LOOP.</span></footer></body></html>\n'
    template = AUTH_LANG.template(template, language)
    body = re.sub(r"@@(CLIENT|REDIRECT|SCOPE|INPUTS|ERROR)@@",
                  lambda match: values[match.group(1)], template)
    social = "" if fields.get("login_ticket") else AUTH_LANG.provider_markup(GITHUB.login_markup(fields) + GOOGLE.login_markup(fields), language)
    body = body.replace('<form method="post" action="/authorize"', social + '<form method="post" action="/authorize"', 1)
    if fields.get("login_ticket"):
        identity = html.escape(str(fields.get("login_identity") or "已登录用户"))
        body = re.sub(r'<label for="password">.*?</p>',
                      lambda _: '<p class="request">' + AUTH_LANG.tr('已验证：', language) + '<strong>' + identity + '</strong>' + AUTH_LANG.tr('。请确认上方客户端和回调地址，再继续授权。', language) + '</p>',
                      body, count=1, flags=re.DOTALL)
    if social:
        body = body.replace('然后输入已有的授权口令继续。', '选择可用的账号登录方式，或使用已有授权口令。')
    if not fields.get("login_ticket"):
        switch = {k: str(v) for k,v in fields.items() if k in keys and k != "login_ticket"}
        switch['lang'] = 'zh' if language == 'en' else 'en'
        label = '简体中文' if language == 'en' else 'English'
        body = body.replace('</header>', '<a href="/authorize?' + html.escape(urlencode(switch), quote=True) + '">' + label + '</a></header>', 1)
    return _text(status, body, "text/html; charset=utf-8", extra={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


def _authorize_get(query, headers=None):
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
        "ui_lang": AUTH_LANG.choose(query.get("lang") or query.get("ui_lang"), headers),
    }
    return _page("", fields)


def _authorize_post(body, headers=None):
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
    who = ((GITHUB.consume_ticket(form, headers or {}) or GOOGLE.consume_ticket(form, headers or {})) if form.get("login_ticket")
           else ACL.match_password(form.get("password") or ""))
    if who is None:
        form.pop("login_ticket", None)
        form.pop("login_identity", None)
        return _page("登录凭据无效或已过期，请重新登录。", form, status=401)
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
    if not ENABLED and not GITHUB.configured() and not GOOGLE.configured():
        return None
    login_response = GITHUB.route(method, path, query, headers, body, sys.modules[__name__])
    if login_response is not None:
        return login_response
    login_response = GOOGLE.route(method, path, query, headers, body, sys.modules[__name__])
    if login_response is not None:
        return login_response
    if path.rstrip("/") == "/.well-known/oauth-protected-resource":
        return _json(200, resource_metadata())
    if path.rstrip("/") == "/.well-known/oauth-authorization-server":
        return _json(200, as_metadata())
    if path == "/register" and method == "POST":
        return _register(body)
    if path == "/authorize":
        if method == "GET":
            return _authorize_get(query, headers)
        if method == "POST":
            return _authorize_post(body, headers)
        return _text(405, "method not allowed", extra={"Allow": "GET, POST"})
    if path == "/token" and method == "POST":
        return _token(body)
    return None
