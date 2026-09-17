"""Local evidence library. Python 3 standard library; no network operations."""
import argparse
import copy
import hashlib
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def save(path, data):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or Path(relative).is_absolute():
        raise ValueError('证据路径必须位于库内')
    return path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def check(root, data):
    if data.get('schema_version') != 1:
        raise ValueError('不支持的数据版本')
    for key in ('records', 'jobs', 'actions'):
        if not isinstance(data.get(key), list):
            raise ValueError(key + ' 必须是列表')
    if not isinstance(data.get('profile'), dict) or not isinstance(data.get('resume'), dict):
        raise ValueError('profile 和 resume 必须是对象')
    if not isinstance(data['profile'].get('name'), str):
        raise ValueError('profile.name 必须是文本，未知可留空')
    if not isinstance(data['resume'].get('direction'), str) or not isinstance(data['resume'].get('summary', ''), str):
        raise ValueError('简历方向和概括必须是文本')
    if not isinstance(data['resume'].get('bullets'), list):
        raise ValueError('resume.bullets 必须是列表')
    facts, record_ids, evidence_ids = {}, set(), set()
    for r in data['records']:
        if not r['id'] or r['id'] in record_ids:
            raise ValueError('经历 ID 缺失或重复')
        record_ids.add(r['id'])
        if r['usage'] not in ('private', 'resume'):
            raise ValueError('未知使用权限')
        for key in ('title', 'raw', 'recorded_at'):
            if not isinstance(r[key], str):
                raise ValueError('记录字段应为文本: ' + key)
        if r.get('occurred') is not None and not isinstance(r['occurred'], str):
            raise ValueError('发生时间应为文本或 null')
        for key in ('tags', 'facts', 'pending', 'evidence'):
            if not isinstance(r.get(key, []), list):
                raise ValueError('记录字段应为列表: ' + key)
        local_ids = set()
        for e in r.get('evidence', []):
            if e['id'] in evidence_ids:
                raise ValueError('证据 ID 重复')
            evidence_ids.add(e['id'])
            local_ids.add(e['id'])
            if 'path' in e:
                p = inside(root, e['path'])
                if not p.is_file() or digest(p) != e['sha256']:
                    raise ValueError('附件缺失或哈希不匹配: ' + e['path'])
            elif not e.get('url', '').startswith(('https://', 'http://')):
                raise ValueError('无效网络证据')
        for f in r.get('facts', []):
            if f['id'] in facts or f['status'] not in ('reported', 'verified', 'uncertain'):
                raise ValueError('事实 ID 重复或状态错误')
            if not set(f.get('evidence_ids', [])).issubset(local_ids):
                raise ValueError('事实引用不存在的证据')
            if f['status'] == 'verified' and not f.get('evidence_ids'):
                raise ValueError('已核实事实需要证据引用')
            facts[f['id']] = (r, f)
    for b in data['resume']['bullets']:
        if not isinstance(b.get('text'), str) or not isinstance(b.get('fact_ids'), list) or not b['fact_ids']:
            raise ValueError('简历条目必须引用事实')
        for fid in b['fact_ids']:
            if fid not in facts:
                raise ValueError('简历引用不存在的事实')
            r, f = facts[fid]
            if r['usage'] != 'resume' or f['status'] == 'uncertain':
                raise ValueError('简历不能引用私密或待核实事实')
    return facts


def resume_text(data):
    p, r = data['profile'], data['resume']
    lines = ['# ' + (p['name'] or '当前简历'), '', r['direction'], '', r.get('summary', ''), '']
    lines.extend('- ' + b['text'] for b in r['bullets'])
    return '\n'.join(lines).strip() + '\n'


def render(root, data):
    check(root, data)
    template = Path(__file__).resolve().parents[1] / 'assets' / 'dashboard.html'
    # Escape HTML delimiters so user text can never terminate the inert JSON block.
    payload = json.dumps(data, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    page = template.read_text(encoding='utf-8').replace('__LIBRARY_DATA__', payload)
    (root / 'index.html').write_text(page, encoding='utf-8')
    (root / 'resume.md').write_text(resume_text(data), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'check', 'render', 'attach', 'snapshot'])
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--record')
    parser.add_argument('--file', type=Path)
    parser.add_argument('--label')
    args = parser.parse_args()
    root = args.root.resolve()
    if root.is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError('个人资料不能存入 Skill 安装目录，请使用独立目录')
    path = root / 'library.json'
    if args.command == 'init':
        root.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            data = dict(schema_version=1, profile=dict(name='', major='', entry_year=None, graduation_year=None, interests=[], intention='尚未确定'), records=[], jobs=[], actions=[], resume=dict(direction='', summary='', bullets=[]))
            # Exclusive create protects an existing library even if another init races.
            with path.open('x', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        render(root, json.loads(path.read_text(encoding='utf-8')))
    else:
        original = path.read_bytes()
        data = json.loads(original)
        check(root, data)
        if args.command == 'attach':
            if not args.record or not args.file or not args.file.is_file():
                raise ValueError('attach 需要有效的 --record 和 --file')
            record = next((r for r in data['records'] if r['id'] == args.record), None)
            if record is None:
                raise ValueError('找不到经历 ID')
            eid = uuid.uuid4().hex
            target = root / 'evidence' / (eid + args.file.suffix)
            target.parent.mkdir(exist_ok=True)
            shutil.copy2(args.file, target)
            record.setdefault('evidence', []).append(dict(id=eid, path=target.relative_to(root).as_posix(), sha256=digest(target), original_name=args.file.name, added_at=now()))
            if path.read_bytes() != original:
                raise ValueError('检测到并发修改，未覆盖数据；新附件已保留在 ' + str(target))
            save(path, data)
            render(root, data)
        elif args.command == 'render':
            render(root, data)
        elif args.command == 'snapshot':
            if not args.label:
                raise ValueError('snapshot 需要 --label')
            render(root, data)
            dest = root / 'snapshots' / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:12])
            dest.mkdir(parents=True, exist_ok=False)
            used = {fid for b in data['resume']['bullets'] for fid in b['fact_ids']}
            frozen = copy.deepcopy(data)
            frozen['records'] = []
            frozen['jobs'], frozen['actions'] = [], []
            for r in data['records']:
                selected = [f for f in r['facts'] if f['id'] in used]
                if not selected:
                    continue
                evidence = {eid for f in selected for eid in f.get('evidence_ids', [])}
                item = copy.deepcopy(r)
                item['facts'] = selected
                item['evidence'] = [e for e in r.get('evidence', []) if e['id'] in evidence]
                frozen['records'].append(item)
                for e in item['evidence']:
                    if 'path' in e:
                        target = inside(dest, e['path'])
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(inside(root, e['path']), target)
            frozen['snapshot'] = dict(label=args.label, created_at=now(), submitted=False)
            save(dest / 'library.json', frozen)
            (dest / 'resume.md').write_text(resume_text(data), encoding='utf-8')
            check(dest, frozen)
            print(dest)
    print('OK:', args.command, root)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit('ERROR: ' + str(error))
