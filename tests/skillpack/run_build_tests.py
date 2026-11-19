"""Source selection and overwrite protection for skill builds."""
from pathlib import Path
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
                    self.assertTrue((skill / 'rules/example.json').is_file())
                with self.assertRaises(FileExistsError):
                    build_skills.build(output)
                self.assertEqual((output / 'mindustry-blueprint/SKILL.md').read_text(), 'blueprint')


if __name__ == '__main__':
    unittest.main()
