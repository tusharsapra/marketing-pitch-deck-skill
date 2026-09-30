#!/usr/bin/env python3
"""Install the same portable skill into local Codex and/or Claude Code."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
import uuid

NAME = 'marketing-pitch-deck-skill'


def install(source, target, backup_root, force=False):
    source, target, backup_root = map(Path, (source, target, backup_root))
    if not (source / 'SKILL.md').is_file():
        raise ValueError(f'No SKILL.md in {source}')
    if target.is_symlink():
        raise ValueError(f'Refusing to replace a symbolic link: {target}')
    if target.exists() and not force:
        raise ValueError(f'Already installed: {target}. Use --force to back up and replace it.')
    token = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    backup_root.mkdir(parents=True, exist_ok=True)
    staging = backup_root / ('staging-' + token)
    backup = None
    try:
        shutil.copytree(source, staging, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = backup_root / (NAME + '-' + token)
            target.rename(backup)
        staging.rename(target)
    except OSError:
        if backup and backup.exists() and not target.exists():
            backup.rename(target)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return backup


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=('codex', 'claude', 'both'), default='both')
    parser.add_argument('--scope', choices=('user', 'project'), default='user')
    parser.add_argument('--project-dir', type=Path, default=Path.cwd())
    parser.add_argument('--force', action='store_true', help='Back up and replace an existing skill')
    args = parser.parse_args(argv)
    source = Path(__file__).resolve().parents[1] / 'skills' / NAME
    base = Path.home() if args.scope == 'user' else args.project_dir.expanduser().resolve()
    agents = ('codex', 'claude') if args.agent == 'both' else (args.agent,)
    destinations = [base / ('.agents' if agent == 'codex' else '.claude') for agent in agents]
    try:
        if not (source / 'SKILL.md').is_file():
            raise ValueError('Run the installer from a complete extracted repository.')
        # Preflight all destinations before replacing anything.
        for parent in destinations:
            target = parent / 'skills' / NAME
            if target.is_symlink() or (target.exists() and not args.force):
                raise ValueError(f'Existing skill at {target}; symbolic links are never replaced. Use --force for a regular folder.')
        for parent in destinations:
            target = parent / 'skills' / NAME
            backup = install(source, target, parent / 'skill-backups', args.force)
            print(f'Installed: {target}')
            if backup:
                print(f'Previous version saved: {backup}')
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
