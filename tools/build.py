"""Build a reproducible release from a fixed public-file allowlist."""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'README.md', 'LICENSE', 'VERSION', 'docs/preview.png',
    'docs/release-notes.md', 'examples/demo.json',
    'tools/install.py', 'tools/demo.py',
    'skills/life-library/SKILL.md', 'skills/life-library/LICENSE',
    'skills/life-library/references/data.md',
    'skills/life-library/assets/dashboard.html',
    'skills/life-library/scripts/library.py',
    'skills/life-library/scripts/test_library.py',
)


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
            info = zipfile.ZipInfo('life-library/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, (ROOT / name).read_bytes())
    skill = archive.with_suffix('.skill')
    with zipfile.ZipFile(skill, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            if name.startswith('skills/life-library/'):
                info = zipfile.ZipInfo(name.removeprefix('skills/'), date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, (ROOT / name).read_bytes())
    manifest = dest / 'SHA256SUMS.txt'
    manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in (archive, skill)), encoding='utf-8', newline='\n')
    print(archive)
    return archive


if __name__ == '__main__':
    build()
