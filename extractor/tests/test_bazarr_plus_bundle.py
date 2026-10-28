"""Offline packaging checks, including real Git provenance and secret exclusion."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('bundle_builder', ROOT / 'scripts/build_bazarr_plus_bundle.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BundleTests(unittest.TestCase):
    def test_reproducible_and_allowlisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / builder.PREFIX
            source.mkdir(parents=True)
            for name in ('provider.py', 'provider.json'):
                (source / name).write_bytes((ROOT / builder.PREFIX / name).read_bytes())
            (source / '.env').write_text('PRIVATE_SENTINEL')
            first = builder.build(repo, repo / 'a.zip')
            second = builder.build(repo, repo / 'b.zip')
            self.assertEqual(first['sha256'], second['sha256'])
            with zipfile.ZipFile(repo / 'a.zip') as z:
                self.assertEqual(sorted(z.namelist()), ['provider.json', 'provider.py'])
                m = json.loads(z.read('provider.json'))
                self.assertEqual(m['files']['provider.py'], hashlib.sha256(z.read('provider.py')).hexdigest())
            self.assertNotIn(b'PRIVATE_SENTINEL', (repo / 'a.zip').read_bytes())
            with self.assertRaises(FileExistsError):
                builder.build(repo, repo / 'a.zip')

    def test_release_reads_commit_not_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / builder.PREFIX
            source.mkdir(parents=True)
            for name in ('provider.py', 'provider.json'):
                (source / name).write_bytes((ROOT / builder.PREFIX / name).read_bytes())
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)
            git('init')
            git('add', '.')
            git('-c', 'user.name=Packaging Test', '-c', 'user.email=test@example.invalid',
                '-c', 'commit.gpgsign=false', 'commit', '-m', 'fixture')
            sha = git('rev-parse', 'HEAD').decode().strip()
            committed = git('show', f'{sha}:{builder.PREFIX}/provider.py')
            (source / 'provider.py').write_text('raise RuntimeError("dirty checkout")')
            report = builder.build(repo, repo / 'release.zip', sha)
            self.assertFalse(report['draft'])
            with zipfile.ZipFile(repo / 'release.zip') as z:
                self.assertEqual(z.read('provider.py'), committed)
                self.assertEqual(json.loads(z.read('provider.json'))['source']['commit'], sha)

    def test_placeholder_and_symbolic_revisions_rejected(self):
        for revision in ('0' * 40, 'main', '--help', 'a' * 39):
            with self.assertRaises(ValueError):
                builder.build(ROOT, ROOT / 'must-not-exist.zip', revision)
