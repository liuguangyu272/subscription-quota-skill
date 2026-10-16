"""Install without replacing any existing skill."""
import argparse
import os
from pathlib import Path
import shutil

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--harness', choices=['codex', 'zcode', 'dsh', 'agents'], default='agents')
    p.add_argument('--dest', type=Path, help='Override parent skills directory, including a project skill root')
    a = p.parse_args()
    base = Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex'))) if a.harness == 'codex' else Path.home()/('.'+a.harness)
    target = (a.dest or base/'skills').expanduser().resolve()/'subscription-quota'
    if target.exists():
        p.error(f'Already exists: {target}; installation will not overwrite it.')
    shutil.copytree(Path(__file__).resolve().parent/'skill/subscription-quota', target,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    print(f'Installed: {target}')
    print('Refresh the harness skill list, then explicitly ask it to use subscription-quota.')
