"""Source selection and overwrite protection for skill builds."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import build_skills


class BuildTests(unittest.TestCase):
    def test_only_canonical_tracked_sources_are_shipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            root.mkdir()
            files = {
                '.dsh/skills/mlog-agentskill/SKILL.md': 'agent',
                'mindustry-blueprint/SKILL.md': 'blueprint',
                'mindustry-blueprint/tools/stale.py': 'old mirror',
                'tools/canonical.py': 'value = 42\n',
                'tools/mlogent/__init__.py': '',
                'tools/mlogent/mcp/__init__.py': '',
                'tools/mlogent/mcp/example.py': 'value = 7\n',
                'tools/mlogent/mcp/data.json': '{}',
                'tools/dev/private.py': 'development only',
                'tools/corpus/private.py': 'corpus only',
                'rules/example.json': '{}',
            }
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            (root / 'tools/private.py').write_text('local scratch', encoding='utf-8')
            output = Path(tmp) / 'skills'
            with patch.object(build_skills, 'ROOT', root):
                build_skills.build(output)
                for skill in output.iterdir():
                    self.assertEqual((skill / 'tools/canonical.py').read_text(), 'value = 42\n')
                    self.assertFalse((skill / 'tools/private.py').exists())
                    self.assertFalse((skill / 'tools/stale.py').exists())
                    self.assertFalse((skill / 'tools/dev').exists())
                    self.assertFalse((skill / 'tools/corpus').exists())
                    self.assertTrue((skill / 'tools/mlogent/__init__.py').is_file())
                    self.assertTrue((skill / 'tools/mlogent/mcp/data.json').is_file())
                    nested = skill / 'tools/mlogent/mcp/example.py'
                    self.assertEqual(nested.read_text(), 'value = 7\n')
                    digest = hashlib.sha256(nested.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                    manifest = (skill / 'tools/MANIFEST.sha256').read_text()
                    self.assertIn(digest + '  mlogent/mcp/example.py\n', manifest)
                    self.assertTrue((skill / 'rules/example.json').is_file())
                with self.assertRaises(FileExistsError):
                    build_skills.build(output)
                self.assertEqual((output / 'mindustry-blueprint/SKILL.md').read_text(), 'blueprint')


if __name__ == '__main__':
    unittest.main()
