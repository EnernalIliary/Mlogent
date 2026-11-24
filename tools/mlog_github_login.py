"""GitHub identity bridge for the existing MCP authorization-code flow.

Provider credentials are server environment values. GitHub access tokens are
used once to read /user and are never persisted or returned to MCP clients.
Pending flows are process-local, browser-bound, expiring and single-use.
"""
import hashlib
import html
from http.cookies import SimpleCookie
import json
import os
import secrets
import threading
import time
from urllib.parse import parse_qs, urlencode
import urllib.request

_LOCK = threading.Lock()
_FLOWS = {}
_TICKETS = {}
TTL = 600
LIMIT = 256
COOKIE = "__Host-mlog_github"
GITHUB_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" focusable="false"><path d="M6.766 11.328c-2.063-.25-3.516-1.734-3.516-3.656 0-.781.281-1.625.75-2.188-.203-.515-.172-1.609.063-2.062.625-.078 1.468.25 1.968.703.594-.187 1.219-.281 1.985-.281.765 0 1.39.094 1.953.265.484-.437 1.344-.765 1.969-.687.218.422.25 1.515.046 2.047.5.593.766 1.39.766 2.203 0 1.922-1.453 3.375-3.547 3.64.531.344.89 1.094.89 1.954v1.625c0 .468.391.734.86.547C13.781 14.359 16 11.53 16 8.03 16 3.61 12.406 0 7.984 0 3.563 0 0 3.61 0 8.031a7.88 7.88 0 0 0 5.172 7.422c.422.156.828-.125.828-.547v-1.25c-.219.094-.5.156-.75.156-1.031 0-1.64-.562-2.078-1.609-.172-.422-.36-.672-.719-.719-.187-.015-.25-.093-.25-.187 0-.188.313-.328.625-.328.453 0 .844.281 1.25.86.313.452.64.655 1.031.655s.641-.14 1-.5c.266-.265.47-.5.657-.656"/></svg>'
FIELDS = ("client_id", "redirect_uri", "state", "code_challenge",
          "code_challenge_method", "scope", "client_name", "ui_lang")


def configured():
    return bool(os.environ.get("MLOG_GITHUB_CLIENT_ID") and
                os.environ.get("MLOG_GITHUB_CLIENT_SECRET"))


def callback(base):
    return base + "/login/github/callback"


def _digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _browser(headers):
    cookie = SimpleCookie()
    try:
        cookie.load(headers.get("Cookie", ""))
        return cookie[COOKIE].value if COOKIE in cookie else ""
    except Exception:
        return ""


def _prune():
    now = time.time()
    for table in (_FLOWS, _TICKETS):
        for key in list(table):
            if table[key]["expires"] <= now:
                del table[key]


def _valid_fields(fields, oauth):
    client = oauth._load()["clients"].get(fields.get("client_id"))
    if not client or fields.get("redirect_uri") not in client["redirect_uris"]:
        return None
    if fields.get("code_challenge_method") != "S256" or not fields.get("code_challenge"):
        return None
    return {**{k: str(fields.get(k) or "") for k in FIELDS},
            "client_name": client.get("client_name") or ""}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _json_request(url, fields=None, token=None):
    headers = {"Accept": "application/json", "User-Agent": "Mlogent-Login/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if fields is not None:
        data = urlencode(fields).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=data, headers=headers)
    # Never forward credentials through a redirect or a third-party mirror.
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=8) as response:
        raw = response.read(256 * 1024 + 1)
        if len(raw) > 256 * 1024:
            raise ValueError("Provider response too large")
        return json.loads(raw)


def _identity(user):
    # Bind to immutable numeric IDs, never a renameable login or matching email.
    subject = user.get("id")
    if type(subject) is not int or subject <= 0 or not isinstance(user.get("login"), str):
        raise ValueError("Missing provider identity")
    return {"name": "github:" + str(subject), "profile": "reader"}


def login_markup(fields):
    if not configured():
        return ""
    hidden = "".join('<input type="hidden" name="%s" value="%s">' %
                     (key, html.escape(str(fields.get(key) or ""), quote=True))
                     for key in FIELDS if key in fields)
    return ('<form method="post" action="/login/github">' + hidden +
            '<button type="submit" style="margin-top:0"><span style="display:inline-flex;align-items:center;gap:10px;font-size:13px;font-weight:600">' + GITHUB_ICON + '使用 GitHub 登录</span>'
            '<span aria-hidden="true">↗</span></button></form>'
            '<p class="field-help" style="margin:12px 0 22px">'
            '使用 GitHub 基础身份登录。新用户使用 reader 权限档。'
            '不读取你的仓库。</p>')


def _start(fields, oauth):
    fields = _valid_fields(fields, oauth)
    if not fields:
        return oauth._text(400, "Invalid MCP authorization request")
    browser, state = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    import base64
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    with _LOCK:
        _prune()
        if len(_FLOWS) >= LIMIT or len(_TICKETS) >= LIMIT:
            return oauth._text(429, "Too many pending logins; retry later")
        _FLOWS[_digest(state)] = {"fields": fields, "browser": _digest(browser),
                                 "verifier": verifier, "expires": time.time() + TTL}
    url = "https://github.com/login/oauth/authorize?" + urlencode({
        "client_id": os.environ["MLOG_GITHUB_CLIENT_ID"],
        "redirect_uri": callback(oauth.BASE), "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
        # Basic public /user information suffices; no email or repository scope.
        "scope": ""})
    return oauth._text(302, "", extra={"Location": url, "Cache-Control": "no-store",
        "Set-Cookie": COOKIE + "=" + browser + "; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=600"})


def _callback(query, headers, oauth):
    browser = _browser(headers)
    with _LOCK:
        _prune()
        key = _digest(query.get("state") or "")
        flow = _FLOWS.get(key)
        if not flow or not browser or not secrets.compare_digest(flow["browser"], _digest(browser)):
            return oauth._text(400, "Login expired or browser state mismatch; restart from your MCP client")
        del _FLOWS[key]
    if query.get("error") or not query.get("code"):
        return oauth._page("GitHub 登录未完成，请重试。", flow["fields"], 400)
    try:
        token = _json_request("https://github.com/login/oauth/access_token", {
            "client_id": os.environ["MLOG_GITHUB_CLIENT_ID"],
            "client_secret": os.environ["MLOG_GITHUB_CLIENT_SECRET"],
            "redirect_uri": callback(oauth.BASE), "code": query["code"],
            "code_verifier": flow["verifier"]})
        access = token.get("access_token")
        if not isinstance(access, str) or not access:
            raise ValueError("Missing access token")
        user = _json_request("https://api.github.com/user", token=access)
        who = _identity(user)
    except Exception:
        # Provider bodies and exception strings may contain secrets.
        return oauth._page("暂时无法完成 GitHub 身份验证，请重新发起连接。", flow["fields"], 502)
    ticket = secrets.token_urlsafe(32)
    with _LOCK:
        _prune()
        if len(_TICKETS) >= LIMIT:
            return oauth._text(429, "Too many pending logins")
        _TICKETS[_digest(ticket)] = {**flow, "who": who, "expires": time.time() + TTL}
    fields = {**flow["fields"], "login_ticket": ticket,
              "login_identity": "GitHub · " + user["login"]}
    response = oauth._page("", fields)
    response[3]["Cache-Control"] = "no-store"
    return response


def consume_ticket(form, headers):
    ticket, browser = form.get("login_ticket"), _browser(headers)
    if not ticket or not browser:
        return None
    with _LOCK:
        _prune()
        key = _digest(ticket)
        item = _TICKETS.get(key)
        if not item or not secrets.compare_digest(item["browser"], _digest(browser)):
            return None
        if any(str(form.get(k) or "") != str(item["fields"].get(k) or "")
               for k in FIELDS if k != "client_name"):
            return None
        del _TICKETS[key]
        return item["who"]


def route(method, path, query, headers, body, oauth):
    if path not in ("/login/github", "/login/github/callback"):
        return None
    if not configured():
        return oauth._text(503, "GitHub sign-in is not configured")
    if path == "/login/github" and method == "POST":
        fields = {k: v[0] for k, v in parse_qs(body.decode("utf-8", "replace")).items()}
        return _start(fields, oauth)
    if path == "/login/github/callback" and method == "GET":
        return _callback(query, headers, oauth)
    return oauth._text(405, "method not allowed")
