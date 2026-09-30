#!/usr/bin/env python3
"""Static package checks, not an evaluation of generated decks."""
import ast
from pathlib import Path
import re
import sys

NAME = 'marketing-pitch-deck-skill'


def validate(root):
    root = Path(root)
    skill = root / 'skills' / NAME
    errors = []
    required = ['README.md', 'LICENSE', 'tools/install_skill.py', 'tests/test_utilities.py',
                'examples/sample-plan.json', f'skills/{NAME}/SKILL.md',
                f'skills/{NAME}/agents/openai.yaml']
    for relative in required:
        if not (root / relative).is_file():
            errors.append(f'Missing {relative}')
    if not (skill / 'SKILL.md').is_file():
        return errors
    text = (skill / 'SKILL.md').read_text(encoding='utf-8')
    match = re.match(r'^---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', text)
    if not match or match.group(1) != NAME:
        errors.append('Shared frontmatter must contain the matching name and description only')
    elif len(match.group(2)) > 1024:
        errors.append('Description exceeds 1024 characters')
    if len(text.splitlines()) >= 500:
        errors.append('Core workflow should stay below 500 lines')
    for path in [skill / 'SKILL.md', *(skill / 'references').glob('*.md')]:
        content = path.read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', content):
            if '://' not in target and not target.startswith('#'):
                if not (path.parent / target.split('#')[0]).is_file():
                    errors.append(f'Broken relative link in {path.relative_to(root)}: {target}')
        if '[TODO' in content:
            errors.append(f'Unfinished placeholder in {path.relative_to(root)}')
    for path in root.rglob('*.py'):
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            errors.append(str(exc))
    for path in root.rglob('*'):
        if path.is_file() and path.suffix in ('.md', '.py', '.json', '.yaml', '.csv'):
            content = path.read_text(encoding='utf-8')
            if re.search(r'/root/\.codex|/workspace/(?:scratch|library)', content):
                errors.append(f'Private runtime path in {path.relative_to(root)}')
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    for error in errors:
        print(f'ERROR: {error}')
    if not errors:
        print('Package checks passed: metadata, required files, links and Python syntax.')
    print('Static checks do not certify compatibility with every agent or deck quality.')
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
