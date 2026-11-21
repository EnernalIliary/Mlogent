"""Per-principal permissions, rate limits and the shared password table.

One password per person; each maps to a profile that decides which tools the
token may call.  Kept out of mlog_oauth.py so the password table can grow
without touching the OAuth state machine.
"""
import hashlib
import hmac
import json
import os
import threading
import time

USERS_FILE = os.environ.get("MLOG_USERS_FILE", "/etc/mlogent/users.json")

DEFAULT_PROFILES = {
    "reader": {
        "label": "只读",
        "rpm": 30,
        "tools": ["mlog_doctor", "mlog_check", "mlog_ir", "mlog_values",
                  "mlog_kb", "mlog_fidelity", "mlog_fetch"],
    },
    "runner": {"label": "全权", "rpm": 120, "tools": ["*"]},
}

_LOCK = threading.Lock()
_BUCKETS = {}


def _table():
    try:
        with open(USERS_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    profiles = dict(DEFAULT_PROFILES)
    configured = data.get("profiles")
    if isinstance(configured, dict):
        profiles.update(configured)
    for name, spec in profiles.items():
        if (not isinstance(spec, dict)
                or not isinstance(spec.get("tools", []), list)
                or any(not isinstance(tool, str) for tool in spec.get("tools", []))):
            profiles[name] = {"label": name, "rpm": 30, "tools": []}
        else:
            try:
                limit = int(spec.get("rpm") or 30)
            except (TypeError, ValueError):
                limit = 30
            profiles[name] = {
                **spec,
                "label": str(spec.get("label") or name),
                "rpm": max(1, min(10_000, limit)),
                "tools": list(spec.get("tools") or []),
            }
    users = [u for u in (data.get("users") or []) if isinstance(u, dict)]
    static_profile = data.get("static_profile", "runner")
    if not isinstance(static_profile, str) or static_profile not in profiles:
        static_profile = "reader"
    return profiles, users, static_profile


def get(name):
    profiles, _, _ = _table()
    return profiles.get(name) or profiles["reader"]


def rpm(name):
    try:
        return max(1, min(10_000, int(get(name).get("rpm") or 30)))
    except (TypeError, ValueError):
        return 30


def static_profile():
    return _table()[2]


def _sha(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def match_password(password):
    """Return {name, profile} for a known password, else None."""
    if not password:
        return None
    _, users, _ = _table()
    digest = _sha(password)
    for user in users:
        stored = str(user.get("password_sha256") or "")
        if stored and hmac.compare_digest(stored, digest):
            return {"name": user.get("name") or "user",
                    "profile": user.get("profile") or "reader"}
    fallback = os.environ.get("MLOG_OAUTH_PASSWORD") or ""
    if fallback and hmac.compare_digest(fallback, password):
        return {"name": "owner", "profile": "runner"}
    return None


def allows(profile, tool):
    allowed = get(profile).get("tools") or []
    return "*" in allowed or tool in allowed


def filter_tools(profile, tools):
    allowed = get(profile).get("tools") or []
    if "*" in allowed:
        return list(tools)
    return [t for t in tools
            if (t.get("name") if isinstance(t, dict) else t) in allowed]


def deny_message(profile, tool):
    prof = get(profile)
    allowed = [x for x in (prof.get("tools") or []) if x != "*"]
    return ("该令牌是「%s」档，没有 %s 的权限。可用：%s。"
            % (prof.get("label") or profile, tool, "、".join(allowed)))


def allow(principal, profile):
    """Sliding-window rate limit; returns (ok, retry_after_seconds)."""
    limit = rpm(profile)
    now = time.time()
    with _LOCK:
        queue = _BUCKETS.setdefault(principal, [])
        while queue and now - queue[0] > 60.0:
            queue.pop(0)
        if len(queue) >= limit:
            return False, max(1, int(60.0 - (now - queue[0])) + 1)
        queue.append(now)
    return True, 0
