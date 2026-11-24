"""Google identity bridge for the existing MCP authorization-code flow.

Provider credentials are server environment values. Google access tokens are
used once at the HTTPS UserInfo endpoint and are never persisted or returned
to MCP clients. ID tokens are not parsed or used as an authentication source.
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
COOKIE = "__Host-mlog_google"
FIELDS = ("client_id", "redirect_uri", "state", "code_challenge",
          "code_challenge_method", "scope", "client_name", "ui_lang")


def configured():
    return (os.environ.get("MLOG_GOOGLE_LOGIN_ENABLED", "1") == "1" and
            bool(os.environ.get("MLOG_GOOGLE_CLIENT_ID") and
                os.environ.get("MLOG_GOOGLE_CLIENT_SECRET"))
            )


def callback(base):
    return base + "/login/google/callback"


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
    # UserInfo is fetched directly from Google with this flow's access token.
    # Bind to Google's stable subject, never merge accounts by matching email.
    subject = user.get("sub")
    if (not isinstance(subject, str) or not subject or len(subject) > 255
            or any(c.isspace() for c in subject)
            or user.get("email_verified") is not True
            or not isinstance(user.get("email"), str) or "@" not in user["email"]):
        raise ValueError("Missing provider identity")
    return {"name": "google:" + str(subject), "profile": "reader"}


def login_markup(fields):
    if not configured():
        return ""
    hidden = "".join('<input type="hidden" name="%s" value="%s">' %
                     (key, html.escape(str(fields.get(key) or ""), quote=True))
                     for key in FIELDS if key in fields)
    return ('<form method="post" action="/login/google">' + hidden +
            '<button type="submit" style="margin-top:0">使用 Google 登录'
            '<span aria-hidden="true">↗</span></button></form>'
            '<p class="field-help" style="margin:12px 0 22px">'
            '使用 Google 基础身份登录。新用户使用 reader 权限档。'
            '仅请求基本身份和已验证邮箱，不读取 Gmail 或云端硬盘。</p>')


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
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": os.environ["MLOG_GOOGLE_CLIENT_ID"],
        "redirect_uri": callback(oauth.BASE), "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
        "response_type": "code", "scope": "openid email profile",
        "access_type": "online", "prompt": "select_account"})
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
        return oauth._page("Google 登录未完成，请重试。", flow["fields"], 400)
    try:
        token = _json_request("https://oauth2.googleapis.com/token", {
            "client_id": os.environ["MLOG_GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["MLOG_GOOGLE_CLIENT_SECRET"],
            "redirect_uri": callback(oauth.BASE), "code": query["code"],
            "code_verifier": flow["verifier"], "grant_type": "authorization_code"})
        access = token.get("access_token")
        if not isinstance(access, str) or not access:
            raise ValueError("Missing access token")
        user = _json_request("https://openidconnect.googleapis.com/v1/userinfo", token=access)
        who = _identity(user)
    except Exception:
        # Provider bodies and exception strings may contain secrets.
        return oauth._page("暂时无法完成 Google 身份验证，请重新发起连接。", flow["fields"], 502)
    ticket = secrets.token_urlsafe(32)
    with _LOCK:
        _prune()
        if len(_TICKETS) >= LIMIT:
            return oauth._text(429, "Too many pending logins")
        _TICKETS[_digest(ticket)] = {**flow, "who": who, "expires": time.time() + TTL}
    fields = {**flow["fields"], "login_ticket": ticket,
              "login_identity": "Google · " + user["email"]}
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
    if path not in ("/login/google", "/login/google/callback"):
        return None
    if not configured():
        return oauth._text(503, "Google sign-in is not configured")
    if path == "/login/google" and method == "POST":
        fields = {k: v[0] for k, v in parse_qs(body.decode("utf-8", "replace")).items()}
        return _start(fields, oauth)
    if path == "/login/google/callback" and method == "GET":
        return _callback(query, headers, oauth)
    return oauth._text(405, "method not allowed")
