"""Exercise the actual release archive and installed skill in an isolated folder."""
import hashlib
import json
import os
import subprocess
import sys
import unittest
import uuid
import zipfile
from pathlib import Path

import build


class DistributionTest(unittest.TestCase):
    def test_download_install_demo_and_reproducibility(self):
        sandbox = build.ROOT / '.tmp' / ('distribution-' + uuid.uuid4().hex)
        sandbox.mkdir(parents=True)
        archive = build.build(sandbox / 'dist')
        first_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        build.build(sandbox / 'dist')
        self.assertEqual(first_hash, hashlib.sha256(archive.read_bytes()).hexdigest())
        with zipfile.ZipFile(archive) as z:
            names = set(z.namelist())
            self.assertEqual(names, {'life-library/' + name for name in build.FILES})
            self.assertFalse(any('__pycache__' in n or '/.tmp/' in n or n.endswith('/library.json') for n in names))
            z.extractall(sandbox / 'unpacked')
        with zipfile.ZipFile(archive.with_suffix('.skill')) as z:
            self.assertIn('life-library/SKILL.md', z.namelist())
            self.assertIn('life-library/LICENSE', z.namelist())
            self.assertNotIn('life-library/examples/demo.json', z.namelist())
        release = sandbox / 'unpacked' / 'life-library'

        def run(script, *args, code=0, env=None):
            result = subprocess.run([sys.executable, '-X', 'utf8', str(script), *map(str, args)], cwd=sandbox, env=env, capture_output=True)
            self.assertEqual(result.returncode, code, result.stderr.decode('utf-8', errors='replace'))
            return result

        installed = sandbox / 'installed skill'
        run(release / 'tools/install.py', '--dest', installed)
        files_before = {p.relative_to(installed): p.read_bytes() for p in installed.rglob('*') if p.is_file()}
        run(release / 'tools/install.py', '--dest', installed, code=1)
        self.assertEqual(files_before, {p.relative_to(installed): p.read_bytes() for p in installed.rglob('*') if p.is_file()})
        env = dict(os.environ, CODEX_HOME=str(sandbox / 'custom codex home'))
        run(release / 'tools/install.py', env=env)
        self.assertTrue((Path(env['CODEX_HOME']) / 'skills/life-library/SKILL.md').is_file())
        data_root = sandbox / '个人资料 with spaces'
        installed_script = installed / 'scripts/library.py'
        run(installed_script, 'init', '--root', data_root)
        run(installed_script, 'check', '--root', data_root)
        run(installed_script, 'init', '--root', installed / 'unsafe-data', code=1)
        self.assertFalse((installed / 'unsafe-data').exists())
        demo_root = sandbox / 'demo'
        run(release / 'tools/demo.py', '--dest', demo_root)
        before = (demo_root / 'library.json').read_bytes()
        run(release / 'tools/demo.py', '--dest', demo_root, code=1)
        self.assertEqual(before, (demo_root / 'library.json').read_bytes())
        demo = json.loads(before)
        self.assertTrue(demo['demo'])
        run(installed_script, 'check', '--root', demo_root)
        run(installed_script, 'render', '--root', demo_root)
        self.assertNotIn('今天发现自己更喜欢', (demo_root / 'resume.md').read_text(encoding='utf-8'))
        self.assertEqual(json.loads((data_root / 'library.json').read_text(encoding='utf-8'))['records'], [])


if __name__ == '__main__':
    unittest.main()
