"""Google bridge contract tests; provider requests are mocked, no real credentials."""
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import mlog_oauth as oauth
import mlog_google_login as google


class Inputs(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.fields = {}
        self.password = False
        self.feed(body.decode())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("name"):
            if attrs.get("type") == "hidden":
                self.fields[attrs["name"]] = attrs.get("value", "")
            if attrs.get("type") == "password":
                self.password = True


class GoogleLogin(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.enterContext(patch.object(oauth, "STORE", self.temp.name + "/oauth.json"))
        self.enterContext(patch.dict(os.environ, {"MLOG_GOOGLE_CLIENT_ID": "fake-client", "MLOG_GOOGLE_CLIENT_SECRET": "NEVER-LEAK", "MLOG_GOOGLE_LOGIN_ENABLED": "1"}))
        google._FLOWS.clear()
        google._TICKETS.clear()
        r = oauth._register(json.dumps({"client_name": "Client <example>", "redirect_uris": ["https://client.example/callback"]}).encode())
        client = json.loads(r[2])
        self.fields = {"client_id": client["client_id"], "redirect_uri": client["redirect_uris"][0],
                       "state": "downstream-state", "code_challenge": "downstream-challenge",
                       "code_challenge_method": "S256", "scope": "mcp", "client_name": "forged-name"}

    def start(self):
        r = google._start(self.fields, oauth)
        self.assertEqual(r[0], 302)
        self.assertIn("Secure; HttpOnly; SameSite=Lax", r[3]["Set-Cookie"])
        self.assertIn("__Host-", r[3]["Set-Cookie"])
        self.cookie = r[3]["Set-Cookie"].split(";", 1)[0]
        self.state = parse_qs(urlsplit(r[3]["Location"]).query)["state"][0]
        return r

    def finish(self):
        self.start()
        with patch.object(google, "_json_request", side_effect=[{"access_token": "transient-token"}, {"sub": "123", "email": "person<script>@example.com", "email_verified": True}]) as request:
            r = google._callback({"state": self.state, "code": "provider-code"}, {"Cookie": self.cookie}, oauth)
        self.assertEqual(r[0], 200)
        self.assertIn("code_verifier", request.call_args_list[0].args[1])
        self.assertNotIn(b"transient-token", r[2])
        self.assertNotIn(b"NEVER-LEAK", r[2])
        self.assertNotIn(b"person<script>", r[2])
        self.assertIn(b"person&lt;script&gt;", r[2])
        self.assertIn("已验证：".encode("utf-8"), r[2])
        self.assertIn("请确认上方客户端和回调地址，再继续授权。".encode("utf-8"), r[2])
        self.assertNotIn(b"????", r[2])
        form = Inputs(r[2])
        self.assertFalse(form.password)
        self.assertIn("login_ticket", form.fields)
        return form.fields

    def test_start_validates_client_and_requests_only_identity_scopes(self):
        bad = {**self.fields, "redirect_uri": "https://attacker.example/"}
        self.assertEqual(google._start(bad, oauth)[0], 400)
        r = self.start()
        query = parse_qs(urlsplit(r[3]["Location"]).query, keep_blank_values=True)
        self.assertEqual(set(query["scope"][0].split()), {"openid", "email", "profile"})
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertNotIn("NEVER-LEAK", r[3]["Location"])

    def test_callback_rejects_wrong_browser_and_replay(self):
        self.start()
        with patch.object(google, "_json_request") as request:
            r = google._callback({"state": self.state, "code": "code"}, {}, oauth)
            self.assertEqual(r[0], 400)
            request.assert_not_called()
        fields = self.finish()
        r = google._callback({"state": self.state, "code": "code"}, {"Cookie": self.cookie}, oauth)
        self.assertEqual(r[0], 400)
        self.assertTrue(fields["login_ticket"])

    def test_identity_requires_stable_verified_subject(self):
        for value in (None, 123, True, "", "bad subject"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                google._identity({"sub": value, "email": "person@example.com", "email_verified": True})

    def test_ticket_is_browser_request_bound_and_single_use(self):
        fields = self.finish()
        self.assertIsNone(google.consume_ticket(fields, {}))
        self.assertIsNone(google.consume_ticket({**fields, "redirect_uri": "https://attacker.example/"}, {"Cookie": self.cookie}))
        who = google.consume_ticket(fields, {"Cookie": self.cookie})
        self.assertEqual(who, {"name": "google:123", "profile": "reader"})
        self.assertIsNone(google.consume_ticket(fields, {"Cookie": self.cookie}))

    def test_confirm_consent_issues_reader_code_with_original_pkce(self):
        fields = self.finish()
        r = oauth._authorize_post(urlencode(fields).encode(), {"Cookie": self.cookie})
        self.assertEqual(r[0], 302)
        qs = parse_qs(urlsplit(r[3]["Location"]).query)
        self.assertEqual(qs["state"], ["downstream-state"])
        entry = oauth._load()["codes"][qs["code"][0]]
        self.assertEqual(entry["profile"], "reader")
        self.assertEqual(entry["user"], "google:123")
        self.assertEqual(entry["code_challenge"], self.fields["code_challenge"])
        self.assertEqual(oauth._authorize_post(urlencode(fields).encode(), {"Cookie": self.cookie})[0], 401)

    def test_expiry_and_provider_errors_fail_closed(self):
        self.start()
        with patch.object(google.time, "time", return_value=10**12):
            self.assertEqual(google._callback({"state": self.state, "code": "code"}, {"Cookie": self.cookie}, oauth)[0], 400)
        self.start()
        with patch.object(google, "_json_request", side_effect=RuntimeError("NEVER-LEAK")):
            r = google._callback({"state": self.state, "code": "code"}, {"Cookie": self.cookie}, oauth)
        self.assertEqual(r[0], 502)
        self.assertNotIn(b"NEVER-LEAK", r[2])

    def test_unconfigured_route_is_unavailable(self):
        with patch.dict(os.environ, {"MLOG_GOOGLE_CLIENT_ID": "", "MLOG_GOOGLE_CLIENT_SECRET": ""}):
            self.assertEqual(google.route("POST", "/login/google", {}, {}, b"", oauth)[0], 503)
            self.assertEqual(google.login_markup(self.fields), "")

    def test_unverified_email_is_rejected(self):
        for verified in (False, None, "true", 1):
            with self.subTest(verified=verified), self.assertRaises(ValueError):
                google._identity({"sub": "123", "email": "person@example.com", "email_verified": verified})

    def test_operator_disabled_login_hides_button_and_blocks_route(self):
        with patch.dict(os.environ, {"MLOG_GOOGLE_LOGIN_ENABLED": "0"}):
            self.assertFalse(google.configured())
            self.assertEqual(google.login_markup(self.fields), "")
            self.assertEqual(google.route("POST", "/login/google", {}, {}, b"", oauth)[0], 503)

    def test_identity_does_not_merge_accounts_by_email(self):
        email = "owner@example.com"
        first = google._identity({"sub": "123", "email": email, "email_verified": True})
        second = google._identity({"sub": "456", "email": email, "email_verified": True})
        self.assertNotEqual(first["name"], second["name"])
        self.assertEqual(first["profile"], "reader")
        self.assertEqual(second["profile"], "reader")


if __name__ == "__main__":
    unittest.main(verbosity=2)
