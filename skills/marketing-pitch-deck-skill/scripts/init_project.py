#!/usr/bin/env python3
"""Copy blank working templates without overwriting existing project files."""
import argparse
from pathlib import Path
import sys


def initialize(destination):
    destination = Path(destination).expanduser().resolve()
    assets = Path(__file__).resolve().parent.parent / 'assets'
    mapping = {
        source: destination / ('research' if source.suffix == '.csv' else '') /
        source.name.replace('.template', '')
        for source in assets.iterdir() if source.is_file()
    }
    conflicts = [str(target) for target in mapping.values() if target.exists()]
    if conflicts:
        raise ValueError('Refusing to overwrite: ' + ', '.join(conflicts))
    for folder in ('research', 'assets/original', 'assets/concepts', 'build', 'output'):
        (destination / folder).mkdir(parents=True, exist_ok=True)
    for source, target in mapping.items():
        target.write_bytes(source.read_bytes())
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', help='Project folder to create or populate')
    args = parser.parse_args()
    try:
        result = initialize(args.destination)
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'Working templates created in {result}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
