"""Install the bundled skill without overwriting an existing installation."""
import argparse
import os
import shutil
from pathlib import Path


def install(dest):
    source = Path(__file__).resolve().parents[1] / 'skills' / 'life-library'
    if not (source / 'SKILL.md').is_file():
        raise ValueError('安装包缺少 skills/life-library/SKILL.md')
    dest = dest.expanduser().resolve()
    if dest.exists():
        raise ValueError('目标已存在，未覆盖；请另选目录或先自行备份旧版: ' + str(dest))
    if dest.is_relative_to(source):
        raise ValueError('安装目标不能位于源 Skill 内部')
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    print('已安装到:', dest)
    print('在下一轮 Codex 对话中使用 $life-library；个人资料请保存在独立目录。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    codex_home = Path(os.environ.get('CODEX_HOME') or (Path.home() / '.codex'))
    parser.add_argument('--dest', type=Path, default=codex_home / 'skills' / 'life-library')
    try:
        install(parser.parse_args().dest)
    except (OSError, ValueError) as error:
        raise SystemExit('ERROR: ' + str(error))
