"""Regression checks with synthetic data, isolated from the user's library."""
import copy
import json
import subprocess
import sys
import uuid
from contextlib import nullcontext
import unittest
from pathlib import Path

import library


class LibraryTest(unittest.TestCase):
    def test_evidence_privacy_and_frozen_version(self):
        sandbox = Path.cwd() / '.tmp' / ('life-library-test-' + uuid.uuid4().hex)
        sandbox.mkdir(parents=True)
        with nullcontext(sandbox) as tmp:
            root = Path(tmp) / 'data'
            script = Path(library.__file__)

            def run(command, *args):
                result = subprocess.run([sys.executable, '-X', 'utf8', str(script), command, '--root', str(root), *args], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
                return result

            run('init')
            path = root / 'library.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            record = dict(id='r1', title='测试经历', kind='课程项目', occurred='2024', recorded_at=library.now(), raw='</script><script>alert(1)</script>', usage='resume', tags=[], pending=['证书待补'], evidence=[], facts=[dict(id='f1', text='完成测试作品', status='reported', evidence_ids=[])])
            data['records'] = [record]
            data['resume']['bullets'] = [dict(text='完成测试作品', fact_ids=['f1'])]
            library.save(path, data)
            before = path.read_bytes()
            run('init')
            self.assertEqual(path.read_bytes(), before, 'init must not reset an existing library')
            source = Path(tmp) / '证据.txt'
            source.write_text('synthetic proof', encoding='utf-8')
            run('attach', '--record', 'r1', '--file', str(source))
            data = json.loads(path.read_text(encoding='utf-8'))
            record = data['records'][0]
            evidence = record['evidence'][0]
            self.assertTrue(source.exists())
            record['facts'][0].update(status='verified', evidence_ids=[evidence['id']])
            library.save(path, data)
            run('snapshot', '--label', '示例留档')
            snapshot = next((root / 'snapshots').iterdir())
            frozen = {p.relative_to(snapshot): p.read_bytes() for p in snapshot.rglob('*') if p.is_file()}
            data['resume']['bullets'][0]['text'] = '更新后的草稿'
            library.save(path, data)
            run('render')
            self.assertEqual(frozen, {p.relative_to(snapshot): p.read_bytes() for p in snapshot.rglob('*') if p.is_file()})
            library.check(snapshot, json.loads((snapshot / 'library.json').read_text(encoding='utf-8')))
            page = (root / 'index.html').read_text(encoding='utf-8')
            self.assertNotIn(record['raw'], page, 'user data must not escape JSON script element')
            for mutation in ('private', 'uncertain', 'missing'):
                invalid = copy.deepcopy(data)
                if mutation == 'private':
                    invalid['records'][0]['usage'] = 'private'
                elif mutation == 'uncertain':
                    invalid['records'][0]['facts'][0]['status'] = 'uncertain'
                else:
                    invalid['resume']['bullets'][0]['fact_ids'] = ['missing']
                with self.assertRaises(ValueError):
                    library.check(root, invalid)
            invalid = copy.deepcopy(data)
            invalid['records'][0]['evidence'][0]['path'] = '../证据.txt'
            with self.assertRaises(ValueError):
                library.check(root, invalid)
            (root / evidence['path']).write_text('tampered', encoding='utf-8')
            with self.assertRaises(ValueError):
                library.check(root, data)


if __name__ == '__main__':
    unittest.main()
