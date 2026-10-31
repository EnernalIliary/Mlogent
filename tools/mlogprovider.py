"""P4 third cut: the model-facing provider for the job queue (offline first).

The queue in tools/jobqueue.py has exactly one seam that may talk to a model:
the callable it stores as ``provider(job, hint) -> dict``.  This module holds the
pieces of that seam so the queue itself stays offline and testable:

* ``build_prompt(job, hint=None)`` -- the three sections of docs/Mlog辅助-规划.md
  section 4.4: world facts (snapshot summary + the link whitelist), a short rule
  summary, and the task with the JSON contract.
* ``parse_reply(text)`` -- pull one JSON object out of a model reply (fenced code
  blocks and prose around it are tolerated) and validate the contract.
* ``HttpProvider`` -- an OpenAI-compatible ``/chat/completions`` call over urllib.
  Nothing here touches the network at import time, and the queue never builds one
  unless the CLI was told to (``--jobs-provider llm --llm-url ...``).
* ``ScriptedProvider`` -- replay recorded replies from a JSON file, so every test
  and every regression run stays offline and deterministic.
* ``Recorder`` -- wrap any provider and append ``{prompt, reply}`` JSONL, so a real
  transcript can be replayed later as a scripted one.
"""

import io
import json
import os
import urllib.error
import urllib.request

MAX_PROMPT_CELLS = 40


class ProviderError(Exception):
    """A reply that cannot be used: bad JSON, missing keys, wrong types."""


def _link_names(links):
    out = []
    for l in links or []:
        if isinstance(l, dict) and l.get("name"):
            out.append(str(l["name"]))
        elif isinstance(l, str):
            out.append(l)
    return out


def snapshot_facts(snap):
    """One short block of world facts out of a region snapshot (never the whole grid)."""
    if not isinstance(snap, dict):
        return ["(no snapshot was sent; assume the processor is alone in an empty area)"]
    rows = []
    b = snap.get("bounds") or {}
    if isinstance(b, dict) and b:
        rows.append("selection: x %s..%s, y %s..%s" % (b.get("x1"), b.get("x2"),
                                                     b.get("y1"), b.get("y2")))
    rows.append("cells in snapshot: %s (truncated: %s)" % (snap.get("cells"),
                                                          bool(snap.get("truncated"))))
    grid = snap.get("grid") or []
    blocks = {}
    for c in grid:
        if isinstance(c, dict):
            k = str(c.get("block") or "air")
            if k != "air":
                blocks[k] = blocks.get(k, 0) + 1
    if blocks:
        top = sorted(blocks.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
        rows.append("blocks nearby: " + ", ".join("%s x%d" % kv for kv in top))
    procs = snap.get("processors") or []
    if procs:
        rows.append("other processors in the snapshot: %d" % len(procs))
    m = snap.get("map")
    if isinstance(m, dict) and m.get("name"):
        rows.append("map: %s" % m.get("name"))
    return rows


def build_prompt(job, hint=None):
    """The three sections of section 4.4, as one string."""
    links = _link_names(job.get("links"))
    origin = job.get("origin") or {}
    ipt = job.get("ipt") or 2
    out = []
    out.append("=== world facts ===")
    if origin:
        out.append("processor tile: (%s, %s); link coordinates are RELATIVE to it" % (
            origin.get("x"), origin.get("y")))
    out.append("instruction set: v160 (ipt=%s)" % ipt)
    out.extend(snapshot_facts(job.get("snapshot")))
    if job.get("links") is None:
        out.append("link whitelist: UNKNOWN (the game could not read the link table).")
        out.append("  Do not invent link names; prefer code that needs no links at all.")
    elif links:
        out.append("link whitelist (the ONLY names allowed as link variables):")
        for l in job.get("links") or []:
            if isinstance(l, dict):
                out.append("  %s @ (%s, %s)" % (l.get("name"), l.get("x"), l.get("y")))
        out.append("  Any other name (container9, core, message2 ...) will be rejected.")
    else:
        out.append("link whitelist: EMPTY -- this processor is wired to nothing.")
        out.append("  Any block-link name in the program will be rejected.")
    out.append("")
    out.append("=== rules ===")
    out.append("- mlog only, one statement per line, no comments, no blank-line tricks.")
    out.append("- A variable is a name used as an operand; assign it before reading it.")
    out.append("- jump <label|line> <condition> <a> <b>; a jump target must exist.")
    out.append("- print/printflush: print writes into the buffer, printflush sends it.")
    out.append("- sensor <result> <block> <property> reads a property of a linked block.")
    out.append("- control/radar/ucontrol need the documented argument count for v160.")
    out.append("- End the program with an explicit `end` unless it loops forever.")
    out.append("- The whole program must pass the analyzer: any ERR rejects the job.")
    out.append("")
    out.append("=== task ===")
    out.append("the player asked for: %s" % (job.get("desc") or ""))
    if hint:
        out.append("")
        out.append("your previous attempt was REJECTED by the gate; fix these findings:")
        for f in hint[:12]:
            if isinstance(f, dict):
                out.append("  line %s: [%s] %s" % (f.get("line"), f.get("sev"), f.get("msg")))
            else:
                out.append("  %s" % (f,))
    out.append("")
    out.append("=== reply ===")
    out.append("Reply with ONE JSON object and nothing else (no prose, no markdown fence).")
    out.append("Anchored tier (pick a known template):")
    out.append('  {"template": "item-threshold", "params": {...}, "explanation": "..."}')
    out.append("Free tier (write the program yourself):")
    out.append('  {"code": "set n 0\\nop add n n 1\\nend", "explanation": "...",')
    out.append('   "assumptions": ["..."], "needs_links": ["container1"]}')
    out.append("needs_links must be a subset of the whitelist above (or empty).")
    return "\n".join(out)


def _first_object(text):
    """The first balanced {...} run in text, or None. Tolerates fences and prose."""
    depth = 0
    start = -1
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                return text[start:i + 1]
    return None


def parse_reply(text):
    """Model reply -> provider dict. Raises ProviderError when unusable."""
    if not isinstance(text, str) or not text.strip():
        raise ProviderError("empty reply")
    blob = _first_object(text)
    if blob is None:
        raise ProviderError("no JSON object in the reply")
    try:
        obj = json.loads(blob)
    except ValueError as exc:
        raise ProviderError("reply JSON does not parse: %s" % exc)
    if not isinstance(obj, dict):
        raise ProviderError("reply JSON is %s, want an object" % type(obj).__name__)
    code = obj.get("code")
    tid = obj.get("template")
    if not (isinstance(code, str) and code.strip()) and not tid:
        raise ProviderError("reply has neither a non-empty code nor a template")
    if code is not None and not isinstance(code, str):
        raise ProviderError("code must be a string")
    if tid is not None and not isinstance(tid, str):
        raise ProviderError("template must be a string")
    params = obj.get("params")
    if params is not None and not isinstance(params, dict):
        raise ProviderError("params must be an object")
    for k in ("assumptions", "needs_links"):
        v = obj.get(k)
        if v is not None and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
            raise ProviderError("%s must be a list of strings" % k)
    out = {"explanation": str(obj.get("explanation") or ""),
           "assumptions": list(obj.get("assumptions") or []),
           "needs_links": list(obj.get("needs_links") or [])}
    if isinstance(code, str) and code.strip():
        out["code"] = code
    if tid:
        out["template"] = tid
        out["params"] = dict(params or {})
    return out


class ScriptedProvider:
    """Replay recorded replies: replies[i] answers the (i+1)-th attempt."""

    def __init__(self, replies, label="scripted"):
        self.replies = list(replies or [])
        self.label = label
        self.prompts = []

    def __call__(self, job, hint=None):
        prompt = build_prompt(job, hint)
        self.prompts.append(prompt)
        if not self.replies:
            return {"error": "scripted provider ran out of replies"}
        item = self.replies.pop(0)
        if isinstance(item, str):
            try:
                return parse_reply(item)
            except ProviderError as exc:
                return {"error": str(exc)}
        if isinstance(item, dict):
            if item.get("raw") is not None:
                try:
                    return parse_reply(str(item["raw"]))
                except ProviderError as exc:
                    return {"error": str(exc)}
            return dict(item)
        return {"error": "scripted reply of type %s" % type(item).__name__}


def load_script(path):
    """Read a replay file: a list of replies, or {"replies": [...]}."""
    with io.open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("replies") or []
    if not isinstance(data, list):
        raise ValueError("a replay file must hold a list of replies")
    return ScriptedProvider(data)


class Recorder:
    """Wrap a provider and append {prompt, reply} to a JSONL file."""

    def __init__(self, inner, path):
        self.inner = inner
        self.path = path

    def __call__(self, job, hint=None):
        prompt = build_prompt(job, hint)
        out = self.inner(job, hint)
        try:
            d = os.path.dirname(os.path.abspath(self.path))
            if d and not os.path.isdir(d):
                os.makedirs(d)
            rec = {"desc": job.get("desc"), "prompt": prompt, "reply": out}
            with io.open(self.path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass
        return out


DEFAULT_MAX_TOKENS = 4096
TOKENS_CEILING = 16000

#: how much of reasoning_content a reply carries back to the job (the panel shows
#: a screenful of it; the point is to explain a refusal, not to archive a transcript)
REASONING_MAX = 12000


class HttpProvider:
    """OpenAI-compatible chat completion, stdlib only, no network at import."""

    def __init__(self, url, model="", key="", timeout=60, temperature=0.2,
                 max_tokens=DEFAULT_MAX_TOKENS, ceiling=TOKENS_CEILING):
        if not url:
            raise ValueError("HttpProvider needs a chat-completions URL")
        self.url = url
        self.model = model
        self.key = key
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = int(max_tokens or DEFAULT_MAX_TOKENS)
        self.ceiling = max(self.max_tokens, int(ceiling or TOKENS_CEILING))

    def __call__(self, job, hint=None):
        prompt = build_prompt(job, hint)
        out = self._once(prompt, self.max_tokens, self.timeout)
        # A reasoning model spends the budget on reasoning_content *before* it writes
        # anything, so a tight max_tokens shows up as 'empty message, finish_reason=length'
        # rather than as a short answer (v0.12.3, measured: 502 prompt tokens, 1600
        # completion tokens, content empty, reasoning_content full).  max_tokens is only a
        # ceiling, so retrying once with a much larger one costs nothing when the first
        # attempt was stopped by the ceiling and not by the model finishing.
        err = out.get("error") or ""
        if "finish_reason=length" in err and self.max_tokens < self.ceiling:
            bigger = min(self.ceiling, self.max_tokens * 4)
            wider = min(600, max(self.timeout, 30) * 3)
            again = self._once(prompt, bigger, wider)
            if not again.get("error"):
                return again
            if "finish_reason=length" in (again.get("error") or ""):
                return _keep_reason({"error": _budget_hint(again["error"], bigger)}, again)
            return again
        if "finish_reason=length" in err:
            return _keep_reason({"error": _budget_hint(err, self.max_tokens)}, out)
        return out

    def _once(self, prompt, budget, timeout):
        body = {"messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": budget}
        if self.model:
            body["model"] = self.model
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.key:
            req.add_header("Authorization", "Bearer " + self.key)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            hint = ""
            if exc.code == 404:
                hint = (" (a 404 usually means the url is the API base, not the full "
                        "chat endpoint -- %s/chat/completions)" % self.url.rstrip("/"))
            body = ""
            try:
                body = exc.read().decode("utf-8", "replace")[:300]
            except Exception:
                body = ""
            return {"error": "model endpoint refused: HTTP %s %s%s%s"
                             % (exc.code, exc.reason, hint,
                                (" | " + body) if body.strip() else "")}
        except urllib.error.URLError as exc:
            return {"error": "model endpoint unreachable: %s" % exc}
        except OSError as exc:
            return {"error": "model call failed: %s" % exc}
        try:
            doc = json.loads(raw)
        except ValueError:
            return {"error": "model endpoint did not answer JSON"}
        text = _reply_text(doc)
        if text is None:
            return _with_reason(
                {"error": "model endpoint answered without a message" + _why_blank(doc)}, doc)
        if not text.strip():
            # An empty content is what a proxy or a token-starved model looks like; the
            # bare 'empty reply' left players guessing, so say what came back instead.
            alt = _alt_text(doc)
            if alt:
                try:
                    return _with_reason(parse_reply(alt), doc)
                except ProviderError:
                    pass
            return _with_reason(
                {"error": "model endpoint answered with an empty message" + _why_blank(doc)}, doc)
        try:
            return _with_reason(parse_reply(text), doc)
        except ProviderError as exc:
            hint = _why_blank(doc)
            return _with_reason(
                {"error": str(exc) + hint if hint else str(exc)}, doc)


def _budget_hint(err, budget):
    """Say what to change when the ceiling -- not the model -- ended the reply."""
    return (err + " -- the %d-token budget ran out before an answer arrived (a reasoning "
                  "model spends it on reasoning_content first); raise it with "
                  "--llm-max-tokens, or use a model that does not reason" % budget)


def _with_reason(res, doc):
    """Carry the model's own thinking back with the reply (v0.12.4).

    The panel shows it, so a refusal explains itself instead of leaving the player
    with 'ERR model endpoint answered with an empty message'.  'reasoning' is the
    endpoint's reasoning_content (or 'reasoning' on providers that name it that
    way); a model that does not reason simply leaves the key out.
    """
    text = _reason_text(doc)
    if text:
        res["reasoning"] = text[:REASONING_MAX]
    return res


def _keep_reason(res, src):
    """Rewriting a reply's error must not throw away the thinking that came with it."""
    if isinstance(src, dict) and src.get("reasoning"):
        res["reasoning"] = src["reasoning"]
    return res


def _reason_text(doc):
    """The reasoning_content / reasoning text of an OpenAI-style reply, or ''."""
    if isinstance(doc, dict):
        choices = doc.get("choices")
        c0 = choices[0] if isinstance(choices, list) and choices else None
        if isinstance(c0, dict):
            msg = c0.get("message")
            if isinstance(msg, dict):
                for key in ("reasoning_content", "reasoning"):
                    v = msg.get(key)
                    if isinstance(v, str) and v.strip():
                        return v
    return ""


def _alt_text(doc):
    """Some endpoints put the answer in reasoning_content instead of content."""
    if isinstance(doc, dict):
        choices = doc.get("choices")
        c0 = choices[0] if isinstance(choices, list) and choices else None
        if isinstance(c0, dict):
            msg = c0.get("message")
            if isinstance(msg, dict):
                for key in ("reasoning_content", "reasoning"):
                    v = msg.get(key)
                    if isinstance(v, str) and v.strip():
                        return v
    return ""


def _why_blank(doc):
    """(finish_reason=length, usage=..., error=...) so a blank reply explains itself."""
    bits = []
    if isinstance(doc, dict):
        choices = doc.get("choices")
        c0 = choices[0] if isinstance(choices, list) and choices else None
        if isinstance(c0, dict):
            fr = c0.get("finish_reason")
            if fr:
                bits.append("finish_reason=%s" % fr)
            msg = c0.get("message")
            if isinstance(msg, dict):
                keys = sorted([str(k) for k in msg.keys()])
                if keys:
                    bits.append("message keys=%s" % ",".join(keys))
        usage = doc.get("usage")
        if isinstance(usage, dict) and usage:
            keep = {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens")
                    if k in usage}
            if keep:
                bits.append("usage=%s" % json.dumps(keep, sort_keys=True))
        if doc.get("error"):
            bits.append("error=%s" % str(doc.get("error"))[:200])
    return (" (" + "; ".join(bits) + ")") if bits else ""


def _reply_text(doc):
    """Pull the assistant text out of an OpenAI-style (or plain) reply."""
    if isinstance(doc, dict):
        choices = doc.get("choices")
        if isinstance(choices, list) and choices:
            c0 = choices[0]
            if isinstance(c0, dict):
                msg = c0.get("message")
                if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                    return msg["content"]
                if isinstance(c0.get("text"), str):
                    return c0["text"]
        if isinstance(doc.get("content"), str):
            return doc["content"]
        if isinstance(doc.get("reply"), str):
            return doc["reply"]
    return None


def provider_from_args(args):
    """Build the provider the CLI asked for, or raise ValueError."""
    kind = getattr(args, "jobs_provider", "template")
    if kind == "fake":
        import jobqueue
        return jobqueue.load_fake_provider(args.fake_provider)
    if kind != "llm":
        return None
    inner = None
    if getattr(args, "llm_replay", None):
        inner = load_script(args.llm_replay)
    elif getattr(args, "llm_url", None):
        key = os.environ.get(args.llm_key_env) if getattr(args, "llm_key_env", None) else ""
        inner = HttpProvider(args.llm_url, model=getattr(args, "llm_model", "") or "",
                             key=key or "", timeout=getattr(args, "llm_timeout", 60),
                             max_tokens=getattr(args, "llm_max_tokens", DEFAULT_MAX_TOKENS)
                             or DEFAULT_MAX_TOKENS)
    else:
        raise ValueError("--jobs-provider llm needs --llm-url or --llm-replay")
    if getattr(args, "llm_record", None):
        return Recorder(inner, args.llm_record)
    return inner
