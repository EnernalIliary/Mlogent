"""The core works without Ops and loads the explicitly configured external package."""
from pathlib import Path
import json
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from world_ops_bridge import load_script, running_description, player_limit, NATIVE_JS


class OpsBridgeTests(unittest.TestCase):
    def test_eight_player_profile_and_invalid_limit_fail_open(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'out/_world').mkdir(parents=True)
            p=root/'out/_world/snapshot-profile.json'
            p.write_text('{"playerLimit":8}')
            self.assertEqual(player_limit(None,root),8)
            for invalid in [-1,True,'8',100000]:
                p.write_text(json.dumps({'playerLimit':invalid}))
                self.assertIsNone(player_limit(None,root))

    def test_running_description_override_preserves_unicode_and_actual_newline(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'out/_world').mkdir(parents=True)
            self.assertEqual(running_description('default',root),'default')
            value='[highlight]Mlogent[white]附属服务器、点个[yellow]\ue809[]吧！\n[gray]\uf308：EnernalIliary/Mlogent'
            (root/'out/_world/snapshot-profile.json').write_text(json.dumps({'runningDescription':value}),encoding='utf-8')
            self.assertEqual(running_description('default',root),value)

    def test_missing_optional_package_keeps_native_core_startup(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{},clear=True):
            error=ModuleNotFoundError('missing optional package',name='mlogent_ops')
            with patch('world_ops_bridge.importlib.import_module',side_effect=error):
                self.assertEqual(load_script(directory),NATIVE_JS)

    def test_persisted_ops_root_is_loaded_on_next_wake(self):
        previous=list(sys.path)
        try:
            with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{},clear=True):
                root=Path(directory);(root/'out/_world').mkdir(parents=True)
                profile=root/'out/_world/snapshot-profile.json'
                profile.write_text(json.dumps({'opsRoot':str(root/'external-ops'),'mode':'experimental'}))
                received=[]
                external=types.SimpleNamespace(startup_script=lambda **kw:received.append(kw) or 'external-script')
                with patch('world_ops_bridge.importlib.import_module',return_value=external) as imported:
                    self.assertEqual(load_script(root),'external-script')
                    imported.assert_called_once_with('mlogent_ops.world_network_policy')
                self.assertEqual(received,[{'profile_path':profile}])
                self.assertEqual(sys.path[0],str((root/'external-ops').resolve()))
        finally:sys.path[:]=previous


if __name__=='__main__':unittest.main()
