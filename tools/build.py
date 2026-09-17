"""Build a reproducible release from a fixed public-file allowlist."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'README.md', 'LICENSE', 'VERSION', 'docs/preview.png',
    'docs/release-notes.md', 'docs/workbuddy.md', 'docs/competitive-landscape.md', 'examples/demo.json',
    'tools/install.py', 'tools/demo.py',
    'skills/life-library/SKILL.md', 'skills/life-library/LICENSE',
    'skills/life-library/references/data.md',
    'skills/life-library/references/workbuddy.md',
    'skills/life-library/assets/dashboard.html',
    'skills/life-library/scripts/library.py',
    'skills/life-library/scripts/test_library.py',
)


def workbuddy_entrypoint(version):
    source = (ROOT / 'skills/life-library/SKILL.md').read_text(encoding='utf-8')
    if not source.startswith('---\n') or '\n---\n' not in source[4:]:
        raise ValueError('源 Skill 缺少 YAML frontmatter')
    frontmatter, body = source[4:].split('\n---\n', 1)
    description = next(line.partition(':')[2].strip() for line in frontmatter.splitlines() if line.startswith('description:'))
    fields = dict(
        name='life-library', display_name='人生库', display_name_en='Life Library',
        description=description,
        description_zh='保存大学经历与成果证据，整理可追溯的简历，讨论下一步成长方向。',
        description_en='Record university experiences and evidence, maintain traceable resume drafts, and explore next steps.',
        category='writing', version=version, author='somnus-J-307',
    )
    header = '\n'.join(key + ': ' + json.dumps(value, ensure_ascii=False) for key, value in fields.items())
    return ('---\n' + header + '\n---\n' + body).encode('utf-8')


def write_entry(z, name, contents):
    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    z.writestr(info, contents)


def build(dest=None):
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    dest = dest or ROOT / 'dist'
    for name in FILES:
        if not (ROOT / name).is_file():
            raise ValueError('缺少发布文件: ' + name)
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / ('life-library-v' + version + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            write_entry(z, 'life-library/' + name, (ROOT / name).read_bytes())
    skill = archive.with_suffix('.skill')
    with zipfile.ZipFile(skill, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            if name.startswith('skills/life-library/'):
                write_entry(z, name.removeprefix('skills/'), (ROOT / name).read_bytes())
    workbuddy = dest / 'life-library-workbuddy.zip'
    with zipfile.ZipFile(workbuddy, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            if name.startswith('skills/life-library/'):
                relative = name.removeprefix('skills/life-library/')
                contents = workbuddy_entrypoint(version) if relative == 'SKILL.md' else (ROOT / name).read_bytes()
                write_entry(z, relative, contents)
    feed = dest / 'workbuddy.json'
    feed.write_text(json.dumps(dict(
        schema_version=1, skill='life-library', display_name='人生库', platform='workbuddy',
        version=version, prerelease=True, install_method='local_zip_import',
        download_url='https://github.com/somnus-J-307/life-library/releases/download/v' + version + '/' + workbuddy.name,
        sha256=hashlib.sha256(workbuddy.read_bytes()).hexdigest(),
        size_bytes=workbuddy.stat().st_size,
        instructions_url='https://github.com/somnus-J-307/life-library/blob/main/docs/workbuddy.md',
        validation=dict(package_and_scripts='automated', desktop_import='not_tested'),
    ), ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    manifest = dest / 'SHA256SUMS.txt'
    manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in (archive, skill, workbuddy, feed)), encoding='utf-8', newline='\n')
    print(archive)
    return archive


if __name__ == '__main__':
    build()
