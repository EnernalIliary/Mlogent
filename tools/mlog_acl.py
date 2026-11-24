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

WORK_TOOLS = frozenset({"mlog_gen", "mlog_inject", "mlog_sim", "mlog_signature_submit"})
READER_FIELDS = {
    "mlog_gen": frozenset({"logic", "name", "links", "blocks", "author", "allow_unsigned"}),
    "mlog_inject": frozenset({"blueprint_code", "index", "mlog", "author", "allow_unsigned",
                              "preview", "expected_sha256"}),
    "mlog_sim": frozenset({"logic", "ticks", "steps", "processor", "world_probe", "power",
                           "power_profile", "marker_preview", "trace_vars", "units", "unit_pos",
                           "core_items", "rt", "update", "links"}),
}


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


def quota_bucket(profile, tool=None):
    return "work" if profile == "reader" and tool in WORK_TOOLS else "default"


def rpm(name, tool=None):
    try:
        work = quota_bucket(name, tool) == "work"
        field, default = ("work_rpm", 10) if work else ("rpm", 30)
        return max(1, min(10_000, int(get(name).get(field) or default)))
    except (TypeError, ValueError):
        return 10 if quota_bucket(name, tool) == "work" else 30


def reader_sim_limits():
    configured = get("reader").get("simulation_limits") or {}
    if not isinstance(configured, dict):
        configured = {}
    result = {}
    for field, default, maximum in (("ticks", 600, 1200), ("steps", 1200, 2400)):
        value = configured.get(field, default)
        result[field] = min(maximum, value) if type(value) is int and value > 0 else default
    return result


def argument_refusal(profile, tool, arguments):
    """Public work uses inline input; it cannot read files or publish world feeds."""
    if profile != "reader":
        return None
    if tool == "mlog_signature_request" and "request_id" not in arguments:
        operation, nested = arguments.get("operation"), arguments.get("arguments")
        if operation in ("mlog_gen", "mlog_inject") and isinstance(nested, dict):
            return argument_refusal(profile, operation, nested)
    allowed = READER_FIELDS.get(tool)
    if allowed is None:
        return None
    extra = sorted(set(arguments) - allowed)
    if extra:
        return "Public offline tools do not accept server paths, projection outputs or these parameters: " + ", ".join(extra)
    required = "blueprint_code" if tool == "mlog_inject" else "logic"
    if not isinstance(arguments.get(required), str) or not arguments[required].strip():
        return "The public profile requires inline " + required + "."
    if tool == "mlog_sim":
        for field, maximum in reader_sim_limits().items():
            if field in arguments and (type(arguments[field]) is not int or not 1 <= arguments[field] <= maximum):
                return "Public simulation {} must be an integer between 1 and {}.".format(field, maximum)
    return None


def public_tool(tool):
    """Advertise the same inline-only contract enforced by argument_refusal."""
    name = tool.get("name")
    if name not in READER_FIELDS:
        return tool
    schema = dict(tool["inputSchema"])
    fields = {k: dict(v) for k, v in schema["properties"].items() if k in READER_FIELDS[name]}
    if name == "mlog_sim":
        for field, limit in reader_sim_limits().items():
            fields[field] = {**fields[field], "maximum": limit}
    schema.pop("oneOf", None)
    schema.update(properties=fields, additionalProperties=False,
                  required=["blueprint_code", "index", "mlog"] if name == "mlog_inject" else ["logic"])
    return {**tool, "inputSchema": schema,
            "description": tool["description"] + " Public profile: inline input only; "
                           "generation, injection and simulation share {} calls/minute.".format(rpm("reader", name))}


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


def allow(principal, profile, tool=None):
    """Sliding-window rate limit; returns (ok, retry_after_seconds)."""
    limit = rpm(profile, tool)
    now = time.time()
    with _LOCK:
        queue = _BUCKETS.setdefault((principal, profile, quota_bucket(profile, tool)), [])
        while queue and now - queue[0] > 60.0:
            queue.pop(0)
        if len(queue) >= limit:
            return False, max(1, int(60.0 - (now - queue[0])) + 1)
        queue.append(now)
    return True, 0
