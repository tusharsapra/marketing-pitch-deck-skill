#!/usr/bin/env python3
"""Report optional local tooling. Do not install dependencies or access accounts."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys


def check(workdir):
    workdir = Path(workdir).expanduser().resolve()
    if not workdir.is_dir():
        raise ValueError(f'Work directory does not exist: {workdir}')
    executables = {name: shutil.which(name) for name in
                   ('python3', 'python', 'node', 'npm', 'soffice', 'libreoffice', 'pdftoppm')}
    pptxgenjs = False
    if executables['node']:
        try:
            result = subprocess.run(
                [executables['node'], '-e', "require.resolve('pptxgenjs')"],
                cwd=workdir, capture_output=True, timeout=10, check=False)
            pptxgenjs = result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            pass
    return {
        'python_version': sys.version.split()[0],
        'python_supported': sys.version_info >= (3, 10),
        'executables': executables,
        'optional_python_modules': {name: importlib.util.find_spec(name) is not None
                                    for name in ('pptx', 'PIL')},
        'pptxgenjs_resolves_from_workdir': pptxgenjs,
        'note': 'Local checks only. Inspect agent-native research/presentation tools separately.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', default='.')
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.workdir), indent=2))
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
