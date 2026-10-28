"""Build an allowlisted, deterministic Provider Hub ZIP without lab secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

PREFIX = 'provider'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def build(repo, output, revision=None):
    repo, output = Path(repo), Path(output)
    if revision:
        # Require an immutable full commit, never an arbitrary Git expression.
        if not re.fullmatch(r'[0-9a-f]{40}', revision) or revision == '0' * 40:
            raise ValueError('Use a real, full 40-character commit SHA')
        resolved = git(repo, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
        if resolved != revision:
            raise ValueError('Revision does not resolve to the requested commit')
        read = lambda name: git(repo, 'show', f'{revision}:{PREFIX}/{name}')
    else:
        read = lambda name: (repo / PREFIX / name).read_bytes()
    code = read('provider.py')
    manifest = json.loads(read('provider.json'))
    if manifest['provider_id'] != 'moonfinbridge':
        raise ValueError('Unexpected provider')
    compile(code, 'provider.py', 'exec')
    manifest['files'] = {'provider.py': hashlib.sha256(code).hexdigest()}
    canonical = b'provider.py\0' + str(len(code)).encode('ascii') + b'\0' + code + b'\0'
    manifest['bundle_sha256'] = hashlib.sha256(canonical).hexdigest()
    manifest['source'].update(commit=revision or '0' * 40, trusted=False)
    if revision:
        manifest['source']['ref'] = revision
    members = {'provider.py': code,
               'provider.json': (json.dumps(manifest, indent=2, ensure_ascii=False) + '\n').encode('utf-8')}
    output.parent.mkdir(parents=True, exist_ok=True)
    # Never silently replace an artifact that may already have been installed.
    with output.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(members):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, members[name])
    return {'path': str(output), 'version': manifest['version'],
            'draft': revision is None, 'source_commit': revision,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--commit', help='Build exclusively from this full Git commit')
    args = parser.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[1], args.output, args.commit), indent=2))
