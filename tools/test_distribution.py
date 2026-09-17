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

    def test_workbuddy_zip_metadata_and_runtime(self):
        sandbox = build.ROOT / '.tmp' / ('workbuddy-' + uuid.uuid4().hex)
        sandbox.mkdir(parents=True)
        build.build(sandbox / 'dist')
        package = sandbox / 'dist/life-library-workbuddy.zip'
        feed = json.loads((sandbox / 'dist/workbuddy.json').read_text(encoding='utf-8'))
        self.assertEqual(feed['sha256'], hashlib.sha256(package.read_bytes()).hexdigest())
        self.assertEqual(feed['size_bytes'], package.stat().st_size)
        version = (build.ROOT / 'VERSION').read_text().strip()
        self.assertEqual(feed['version'], version)
        self.assertIn('/v' + version + '/', feed['download_url'])
        self.assertEqual(feed['validation']['desktop_import'], 'not_tested')
        installed = sandbox / 'workbuddy skill'
        with zipfile.ZipFile(package) as z:
            expected = {name.removeprefix('skills/life-library/') for name in build.FILES if name.startswith('skills/life-library/')}
            self.assertEqual(set(z.namelist()), expected)
            entrypoint = z.read('SKILL.md').decode('utf-8')
            header, body = entrypoint[4:].split('\n---\n', 1)
            fields = {key: json.loads(value.strip()) for key, value in (line.split(':', 1) for line in header.splitlines())}
            for key in ('description', 'description_zh', 'description_en', 'version', 'author'):
                self.assertTrue(fields[key])
            self.assertEqual(fields['version'], version)
            self.assertEqual(fields['name'], 'life-library')
            self.assertEqual(body, (build.ROOT / 'skills/life-library/SKILL.md').read_text(encoding='utf-8')[4:].split('\n---\n', 1)[1])
            for name in z.namelist():
                if name != 'SKILL.md':
                    self.assertEqual(z.read(name), (build.ROOT / 'skills/life-library' / name).read_bytes())
            z.extractall(installed)
        script = installed / 'scripts/library.py'
        data_root = sandbox / '私人资料'
        for command in ('init', 'check', 'render'):
            result = subprocess.run([sys.executable, '-X', 'utf8', str(script), command, '--root', str(data_root)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
        self.assertTrue((data_root / 'index.html').is_file())
        # Exercise attachment copying, evidence restrictions and frozen snapshots using the extracted package itself.
        result = subprocess.run([sys.executable, '-X', 'utf8', str(installed / 'scripts/test_library.py')], cwd=sandbox, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))


if __name__ == '__main__':
    unittest.main()
