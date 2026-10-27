#!/usr/bin/env python3
"""Link selected skills into a local discovery directory without overwriting conflicts."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def inventory(directory):
    result = {}
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Cannot adopt a directory containing symlinks: {directory}')
        result[str(path.relative_to(directory))] = None if path.is_dir() else path.read_bytes()
    return result


def install(sources, target, *, adopt_identical=False, dry_run=False):
    target = target.expanduser().resolve()
    plan = []
    # Preflight every selected skill before changing any destination.
    for source in sources:
        source = source.resolve()
        if not (source / 'SKILL.md').is_file():
            raise ValueError(f'Missing skill manifest: {source}')
        if target == source or source in target.parents:
            raise ValueError(f'Discovery directory must be outside the source skill: {source}')
        destination = target / source.name
        if destination == source:
            raise ValueError(f'Discovery destination is the source skill itself: {source}')
        if destination.is_symlink():
            if destination.resolve() != source:
                raise ValueError(f'Existing link points elsewhere: {destination}')
            plan.append(('keep', source, destination))
        elif destination.exists():
            if not (adopt_identical and destination.is_dir() and inventory(destination) == inventory(source)):
                raise ValueError(f'Existing path preserved: {destination}; only identical directories can be adopted.')
            plan.append(('adopt', source, destination))
        else:
            plan.append(('link', source, destination))

    for operation, source, destination in plan:
        print(f'{"PLAN " if dry_run else ""}{operation}: {destination} -> {source}')
        if dry_run or operation == 'keep':
            continue
        target.mkdir(parents=True, exist_ok=True)
        backup = None
        if operation == 'adopt':
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = target.parent / 'skill-backups' / 'skill-foundry' / f'{source.name}-{stamp}'
            backup.parent.mkdir(parents=True, exist_ok=True)
            destination.rename(backup)
        try:
            destination.symlink_to(source, target_is_directory=True)
        except OSError:
            if backup is not None and not destination.exists() and not destination.is_symlink():
                backup.rename(destination)
            raise
        if backup:
            print(f'Backup preserved: {backup}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('names', nargs='*', help='Skill folder names; default: all skills in this repository.')
    parser.add_argument('--target', type=Path, default=Path.home() / '.agents/skills')
    parser.add_argument('--adopt-identical', action='store_true', help='Back up identical directories and replace with links.')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    names = args.names or sorted(path.name for path in (ROOT / 'skills').iterdir() if path.is_dir())
    if not names or len(names) != len(set(names)):
        parser.error('Choose one or more distinct skill names.')
    if any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) for name in names):
        parser.error('Skill names must use lowercase letters, digits and hyphens.')
    try:
        install([ROOT / 'skills' / name for name in names], args.target,
                adopt_identical=args.adopt_identical, dry_run=args.dry_run)
    except (ValueError, OSError) as error:
        sys.exit(str(error))


if __name__ == '__main__':
    main()
