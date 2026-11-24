import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import mlog_oauth as oauth
import mlog_auth_i18n as i18n
import mlog_github_login as github
import mlog_google_login as google

class AuthLanguageTests(unittest.TestCase):
    def setUp(self):
        self.fields={'client_id':'client','redirect_uri':'https://example.test/callback','state':'state','code_challenge':'challenge','code_challenge_method':'S256','scope':'mcp','client_name':'Client <example>'}

    def test_browser_language_and_explicit_override(self):
        self.assertEqual(i18n.choose(None,{'Accept-Language':'en-US,en;q=0.9'}),'en')
        self.assertEqual(i18n.choose(None,{'Accept-Language':'zh-TW,en;q=0.9'}),'zh')
        self.assertEqual(i18n.choose(None,{'Accept-Language':'de-DE'}),'en')
        self.assertEqual(i18n.choose('zh',{'Accept-Language':'en'}),'zh')

    def test_english_consent_retains_metadata_and_form_parameters(self):
        fields={**self.fields,'ui_lang':'en','state':'中文 state<&"'}
        with patch.dict(os.environ,{'MLOG_GITHUB_CLIENT_ID':'test','MLOG_GITHUB_CLIENT_SECRET':'test'}):
            r=oauth._page('登录凭据无效或已过期，请重新登录。',fields,401)
        body=r[2].decode()
        self.assertEqual(r[0],401)
        self.assertIn('lang="en"',body)
        self.assertIn('Sign in with GitHub',body)
        self.assertIn('Sign-in credentials are invalid',body)
        self.assertIn('Client &lt;example&gt;',body)
        self.assertIn('中文 state&lt;&amp;&quot;',body)
        self.assertIn('name="ui_lang" value="en"',body)
        self.assertNotIn('>授权口令<',body)

    def test_verified_english_consent_has_no_password_and_does_not_leak_ticket_in_switch_url(self):
        r=oauth._page('',{**self.fields,'ui_lang':'en','login_identity':'GitHub · test','login_ticket':'private-ticket'})
        body=r[2].decode()
        self.assertIn('Verified: ',body)
        self.assertIn('Check the client and callback above',body)
        self.assertNotIn('type="password"',body)
        self.assertNotIn('href="/authorize?',body)
        self.assertNotIn('????',body)

    def test_get_chooses_browser_language_and_provider_flows_preserve_it(self):
        client={'client_id':'client','client_name':'Example','redirect_uris':[self.fields['redirect_uri']]}
        with patch.object(oauth,'_load',return_value={'clients':{'client':client}}):
            r=oauth._authorize_get(self.fields,{'Accept-Language':'en'})
            self.assertIn(b'name="ui_lang" value="en"',r[2])
            for provider in (github,google):
                fields=provider._valid_fields({**self.fields,'ui_lang':'en'},oauth)
                self.assertEqual(fields['ui_lang'],'en')
                self.assertIn('ui_lang',provider.FIELDS)

if __name__=='__main__':unittest.main(verbosity=2)
