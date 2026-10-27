#!/usr/bin/env python3
"""Validate skill metadata and relative Markdown file links."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    sys.exit('Install development dependencies: python3 -m pip install -r requirements-dev.txt')

ROOT = Path(__file__).resolve().parents[1]


def check():
    errors = []
    skills = sorted(path for path in (ROOT / 'skills').iterdir() if path.is_dir())
    if not skills:
        errors.append('No skills found.')
    for skill in skills:
        manifest = skill / 'SKILL.md'
        if not manifest.is_file():
            errors.append(f'{skill.name}: missing SKILL.md')
            continue
        text = manifest.read_text(encoding='utf-8')
        match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
        try:
            data = yaml.safe_load(match[1]) if match else None
        except yaml.YAMLError as error:
            errors.append(f'{skill.name}: invalid frontmatter: {error}')
            continue
        if not isinstance(data, dict):
            errors.append(f'{skill.name}: frontmatter must be a YAML mapping')
            continue
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill.name) or len(skill.name) > 64:
            errors.append(f'{skill.name}: invalid folder name')
        if data.get('name') != skill.name:
            errors.append(f'{skill.name}: frontmatter name must match folder')
        if not isinstance(data.get('description'), str) or not data['description'].strip():
            errors.append(f'{skill.name}: description must be a nonempty string')
        ui = skill / 'agents/openai.yaml'
        if ui.exists():
            try:
                if not isinstance(yaml.safe_load(ui.read_text(encoding='utf-8')), dict):
                    errors.append(f'{ui.relative_to(ROOT)}: expected YAML mapping')
            except yaml.YAMLError as error:
                errors.append(f'{ui.relative_to(ROOT)}: invalid YAML: {error}')
        for doc in skill.rglob('*.md'):
            for target in re.findall(r'\]\(([^)\s]+)\)', doc.read_text(encoding='utf-8')):
                parsed = urlsplit(target.strip('<>'))
                if parsed.scheme or not parsed.path:
                    continue
                path = Path(unquote(parsed.path))
                if path.is_absolute():
                    errors.append(f'{doc.relative_to(ROOT)}: use portable relative link: {target}')
                elif not (doc.parent / path).exists():
                    errors.append(f'{doc.relative_to(ROOT)}: missing link target: {target}')
    if errors:
        sys.exit('\n'.join(errors))
    print(f'Validated {len(skills)} skill(s): metadata and relative file links.')


if __name__ == '__main__':
    check()
