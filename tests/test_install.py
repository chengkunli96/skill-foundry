import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('skill_install', Path(__file__).resolve().parents[1] / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'repo/skills/example'
        self.source.mkdir(parents=True)
        (self.source / 'SKILL.md').write_text('example')
        self.target = self.root / 'user/skills'

    def test_install_and_repeat_keep_live_source(self):
        installer.install([self.source], self.target)
        link = self.target / 'example'
        self.assertTrue(link.is_symlink())
        installer.install([self.source], self.target)
        (self.source / 'SKILL.md').write_text('updated')
        self.assertEqual((link / 'SKILL.md').read_text(), 'updated')

    def test_preflight_conflict_preserves_all_destinations(self):
        other = self.source.parent / 'other'
        other.mkdir()
        (other / 'SKILL.md').write_text('other')
        self.target.mkdir(parents=True)
        conflict = self.target / 'other'
        conflict.write_text('preserve me')
        with self.assertRaises(ValueError):
            installer.install([self.source, other], self.target)
        self.assertFalse((self.target / 'example').exists())
        self.assertEqual(conflict.read_text(), 'preserve me')

    def test_identical_directory_is_backed_up_before_linking(self):
        old = self.target / 'example'
        old.mkdir(parents=True)
        (old / 'SKILL.md').write_text('example')
        installer.install([self.source], self.target, adopt_identical=True)
        self.assertTrue(old.is_symlink())
        backups = list((self.target.parent / 'skill-backups/skill-foundry').iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'SKILL.md').read_text(), 'example')

    def test_different_content_is_preserved_even_when_adopting(self):
        old = self.target / 'example'
        old.mkdir(parents=True)
        (old / 'SKILL.md').write_text('local changes')
        with self.assertRaises(ValueError):
            installer.install([self.source], self.target, adopt_identical=True)
        self.assertFalse(old.is_symlink())
        self.assertEqual((old / 'SKILL.md').read_text(), 'local changes')

    def test_foreign_or_broken_link_is_preserved(self):
        self.target.mkdir(parents=True)
        link = self.target / 'example'
        link.symlink_to(self.root / 'missing')
        with self.assertRaises(ValueError):
            installer.install([self.source], self.target, adopt_identical=True)
        self.assertEqual(link.readlink(), self.root / 'missing')

    def test_dry_run_makes_no_directories(self):
        installer.install([self.source], self.target, dry_run=True)
        self.assertFalse(self.target.exists())

    def test_installing_over_source_is_rejected(self):
        with self.assertRaises(ValueError):
            installer.install([self.source], self.source.parent, adopt_identical=True)
        self.assertTrue(self.source.is_dir())
        self.assertFalse(self.source.is_symlink())

    def test_failed_link_restores_adopted_directory(self):
        old = self.target / 'example'
        old.mkdir(parents=True)
        (old / 'SKILL.md').write_text('example')
        with patch.object(Path, 'symlink_to', side_effect=OSError('link unavailable')):
            with self.assertRaises(OSError):
                installer.install([self.source], self.target, adopt_identical=True)
        self.assertFalse(old.is_symlink())
        self.assertEqual((old / 'SKILL.md').read_text(), 'example')


if __name__ == '__main__':
    unittest.main()
