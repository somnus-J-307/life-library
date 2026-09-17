"""Create an explicitly synthetic demo in a new directory."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills' / 'life-library' / 'scripts'))
import library


def create(dest):
    dest = dest.expanduser().resolve()
    # Refuse even empty existing folders so demo data never enters a real library.
    dest.mkdir(parents=True, exist_ok=False)
    data = json.loads((ROOT / 'examples' / 'demo.json').read_text(encoding='utf-8'))
    library.check(dest, data)
    library.save(dest / 'library.json', data)
    library.render(dest, data)
    print('虚构演示，不是真实个人档案:', dest / 'index.html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True, type=Path)
    try:
        create(parser.parse_args().dest)
    except (ValueError, OSError) as error:
        raise SystemExit('ERROR: ' + str(error))
