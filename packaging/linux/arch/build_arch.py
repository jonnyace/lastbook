#!/usr/bin/env python3
"""Prepare a selected local checkout and wheels, then build with native makepkg.

Online preparation runs the existing TLS gate. makepkg has only local,
checksummed sources and installs wheels into its build tree, never system Python.
No dependency installation, package installation, signing or publication occurs.
"""
import argparse
from email.parser import Parser
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from stage_linux import ASSETS, PROGRAM_FILES, checked, copy_file, tree_files


def sha256(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def wheel_lock(directory):
    """Pin every resolved wheel, including transitive dependencies, by content."""
    lines, names = [], set()
    for rel in tree_files(directory):
        if len(rel.parts) != 1 or rel.suffix != '.whl':
            raise ValueError(f'expected only wheels: {rel}')
        wheel = directory / rel
        with zipfile.ZipFile(wheel) as z:
            metadata = [n for n in z.namelist() if re.fullmatch(r'[^/]+\.dist-info/METADATA', n)]
            if len(metadata) != 1:
                raise ValueError(f'invalid wheel metadata: {rel}')
            info = Parser().parsestr(z.read(metadata[0]).decode('utf-8'))
        name, version = info.get('Name', ''), info.get('Version', '')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.!+_-]*', version):
            raise ValueError(f'invalid wheel name/version: {rel}')
        name = re.sub(r'[-_.]+', '-', name).lower()
        if name in names:
            raise ValueError(f'duplicate wheel distribution: {name}')
        names.add(name)
        lines.append(f'{name}=={version} --hash=sha256:{sha256(wheel)}')
    if not lines:
        raise ValueError('no wheels resolved')
    return '\n'.join(sorted(lines)) + '\n'


def snapshot(dest):
    """Explicit program list plus tracked public UI assets; no checkout sweep."""
    support = ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'packaging/ship_app_files.py', 'packaging/ship_edits.json',
               'packaging/check_tls_roots.py', 'packaging/linux/stage_linux.py', 'packaging/linux/scan_package_linux.py',
               'packaging/linux/requirements_linux.txt', 'packaging/linux/gst/lastbooksrc.c')
    files = list(PROGRAM_FILES) + list(ASSETS) + list(support)
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z', '--', 'web', 'content/gaps.json', 'content/topics'],
                             env={'PATH': '/usr/bin:/bin', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull},
                             check=True, capture_output=True).stdout.decode('utf-8').split('\0')
    edits = json.loads(checked(ROOT / 'packaging/ship_edits.json').read_text(encoding='utf-8'))
    for rel in filter(None, tracked):
        p = Path(rel)
        if p.name in edits['never_ship'] or p.name == '.DS_Store':
            continue
        # .woff2 and .txt are web's heading font and the licence its OFL requires shipping beside it.
        allowed = ((len(p.parts) == 2 and p.parts[0] == 'web' and p.suffix in {'.html', '.css', '.js', '.json', '.webmanifest', '.svg', '.png', '.woff2', '.txt'})
                   or rel == 'content/gaps.json'
                   or (len(p.parts) == 3 and p.parts[:2] == ('content', 'topics') and p.suffix == '.json'))
        if not allowed or any(part.startswith('.') for part in p.parts):
            raise ValueError(f'unexpected tracked asset: {rel}')
        files.append(rel)
    for rel in files:
        copy_file(ROOT / rel, dest / rel)


def archive(prepared, target):
    with tarfile.open(target, 'w') as tar:
        for rel in tree_files(prepared):
            path = prepared / rel
            info = tar.gettarinfo(str(path), arcname='lastbook/' + rel.as_posix())
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            info.mtime = 0
            info.mode = 0o644
            with path.open('rb') as f:
                tar.addfile(info, f)


def is_arch(os_release):
    """Omarchy identifies itself separately and declares Arch in ID_LIKE."""
    return os_release.get('ID') == 'arch' or 'arch' in os_release.get('ID_LIKE', '').split()


def release_version():
    """The Ubuntu build's release number, so both Linux packages of one checkout agree."""
    text = (HERE.parent / 'build_app_linux.sh').read_text(encoding='utf-8')
    match = re.search(r'^APP_VERSION="\$\{LASTBOOK_VERSION:-([0-9][0-9A-Za-z.]*)\}"$', text, re.M)
    if not match:
        raise ValueError('cannot read the release version from build_app_linux.sh; pass --version')
    return match[1]


def prerequisites():
    if platform.machine() != 'x86_64' or not is_arch(platform.freedesktop_os_release()):
        raise ValueError('build on native Arch Linux / Omarchy, x86_64')
    if os.geteuid() == 0:
        raise ValueError('run as an ordinary user; makepkg refuses root')
    if Path(sys.executable).resolve() != Path('/usr/bin/python3').resolve() or sys.implementation.name != 'cpython' or sysconfig.get_config_var('Py_GIL_DISABLED'):
        raise ValueError('use Arch /usr/bin/python3 (standard CPython ABI)')
    for command in ('git', 'makepkg', 'pacman', 'gcc', 'pkg-config', 'readelf', 'nm', 'bsdtar', 'zstd', 'fakeroot'):
        if not shutil.which(command, path='/usr/bin:/bin'):
            raise ValueError(f'missing prerequisite: {command}; see packaging/linux/arch/README.md')
    subprocess.run(['pkg-config', '--exists', 'gstreamer-1.0', 'gstreamer-base-1.0'], check=True)
    missing = subprocess.run(['pacman', '-T', 'python-pip', 'python-pillow', 'python-gobject', 'gtk3',
                              'webkit2gtk-4.1>=2.40', 'libsoup3', 'gstreamer', 'gst-plugins-base',
                              'gst-plugins-good', 'gst-libav', 'gst-plugins-bad-libs', 'gst-plugin-dav1d',
                              'gcc-libs'], capture_output=True, text=True)
    if missing.returncode:
        raise ValueError('missing Arch dependencies: ' + (missing.stdout or missing.stderr).strip())
    # After the pacman check, so a stock Arch install (python ships without pip) gets the sentence above
    # instead of a bare ModuleNotFoundError traceback from the probe.
    probe = subprocess.run([sys.executable, '-I', '-B', '-c', 'import pip; from PIL import Image'],
                           capture_output=True, text=True)
    if probe.returncode:
        raise ValueError('python-pip/python-pillow are installed but do not import: '
                         + (probe.stderr or probe.stdout).strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', type=Path, required=True, help='explicit verified public setup manifest-v1.json')
    ap.add_argument('--version', default=None, help='package version; default: the release in build_app_linux.sh')
    ap.add_argument('--llm', type=Path,
                    help='directory holding a built lastbook-llm runner (output of '
                         'packaging/llm/build_llm_linux.sh); bundled as /opt/lastbook/llm')
    args = ap.parse_args()
    args.version = args.version or release_version()
    llm = None
    if args.llm:
        llm = checked(args.llm, directory=True)
        runner = llm / 'lastbook-llm'
        if not runner.is_file() or not os.access(runner, os.X_OK):
            raise ValueError(f'{llm} has no executable lastbook-llm')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9A-Za-z]+)*', args.version):
        raise ValueError('version must contain only dot-separated alphanumeric components, starting with digits')
    manifest_file = checked(args.manifest)
    # Use the real setup schema and download-host allowlist, without fetching or
    # inventing release records. Preserve the supplied manifest bytes exactly.
    sys.path.insert(0, str(ROOT))
    from engine.setup.manifest import validate
    manifest_bytes = manifest_file.read_bytes()
    try:
        validated = validate(json.loads(manifest_bytes))
    except (TypeError, KeyError):
        validated = None
    if not validated or not any(p['available'] for p in validated['packs']):
        raise ValueError('manifest must pass setup validation and contain an available pack')
    prerequisites()
    base = Path(os.path.abspath(os.environ.get('TMPDIR') or ROOT / 'derived/app-build/arch'))
    if any(p.is_symlink() for p in (base, *base.parents)):
        raise ValueError('scratch directory must not have symlink ancestors')
    if re.search(r'/(?:home|Users|root)(?:/|$)', str(base)):
        raise ValueError('makepkg records build paths: set TMPDIR to a neutral scratch directory, such as /tmp')
    base.mkdir(parents=True, exist_ok=True)
    checked(base, directory=True)
    out = Path(tempfile.mkdtemp(prefix='lastbook-arch-', dir=base)).resolve()
    print(f'Build directory: {out}', flush=True)
    prepared, source = out / 'prepared', out / 'prepared/source'
    for name in ('tmp', 'config', 'packages', 'logs'):
        (out / name).mkdir()
    # No user pip/makepkg config, credentials, caches, signing keys, or compiler
    # environment. System makepkg.conf supplies Arch's build flags only.
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'TMPDIR': str(out / 'tmp'),
           'XDG_CONFIG_HOME': str(out / 'config'), 'NETRC': os.devnull, 'PYTHONDONTWRITEBYTECODE': '1'}

    def run(argv, log=None):
        if log:
            with (out / 'logs' / log).open('w') as f:
                subprocess.run(argv, cwd=out, env=env, stdout=f, stderr=subprocess.STDOUT, check=True)
        else:
            subprocess.run(argv, cwd=out, env=env, check=True)

    snapshot(source)
    run([sys.executable, '-I', '-B', str(source / 'packaging/ship_app_files.py'), str(prepared / 'ship')])
    (prepared / 'ship/setup').mkdir()
    (prepared / 'ship/setup/manifest-v1.json').write_bytes(manifest_bytes)
    # Always mandatory. No SKIP_TLS_GATE option for this workflow.
    run([sys.executable, '-I', '-B', str(source / 'packaging/check_tls_roots.py')], 'tls.txt')
    wheels = prepared / 'wheels'
    wheels.mkdir()
    run([sys.executable, '-I', '-B', '-m', 'pip', '--isolated', '--disable-pip-version-check', 'download',
         '--no-cache-dir', '--only-binary=:all:', '--index-url', 'https://pypi.org/simple',
         '--dest', str(wheels), '-r', str(source / 'packaging/linux/requirements_linux.txt')], 'wheels.txt')
    (prepared / 'wheels.lock').write_text(wheel_lock(wheels), encoding='utf-8')
    tar = out / 'lastbook-source.tar'
    archive(prepared, tar)
    py = sys.version_info
    template = checked(HERE / 'PKGBUILD.in').read_text(encoding='utf-8')
    values = {'VERSION': args.version, 'PYTHON': f'{py.major}.{py.minor}',
              'PYTHON_NEXT': f'{py.major}.{py.minor + 1}', 'SOURCE_SHA256': sha256(tar),
              'LLM_SOURCE': '', 'LLM_SHA256': '', 'LLM_ARGS': ''}
    if llm:
        # The runner travels as its own source so the payload keeps its executable bits
        # and libllama.so beside it, exactly as the Debian build lays it out.
        llm_tar = out / 'lastbook-llm.tar'
        with tarfile.open(llm_tar, 'w') as t:
            for path in sorted(llm.rglob('*')):
                if path.is_file() and not path.is_symlink():
                    t.add(str(path), arcname='llm-runner/' + path.relative_to(llm).as_posix())
        values.update({'LLM_SOURCE': "'lastbook-llm.tar'", 'LLM_SHA256': f"'{sha256(llm_tar)}'",
                       'LLM_ARGS': '--llm "$srcdir/llm-runner"'})
    for key, value in values.items():
        template = template.replace('@' + key + '@', value)
    (out / 'PKGBUILD').write_text(template, encoding='utf-8')
    # Paths are resolved from the generated build directory. Never source a
    # person's makepkg config or let configured output paths escape this build.
    config = out / 'makepkg.conf'
    config.write_text('source /etc/makepkg.conf\n'
                      'BUILDDIR="$PWD/work"\nPKGDEST="$PWD/packages"\nSRCDEST="$PWD"\nLOGDEST="$PWD/logs"\n'
                      'PACKAGER="Lastbook local build"\nPKGEXT=".pkg.tar.zst"\n'
                      'BUILDENV=(!distcc color !ccache check !sign)\n', encoding='utf-8')
    run(['makepkg', '--config', str(config), '--cleanbuild', '--noconfirm'], 'makepkg.txt')
    packages = list((out / 'packages').glob('lastbook-*.pkg.tar.zst'))
    if len(packages) != 1:
        raise ValueError('expected exactly one native Arch package')
    # Native package provenance is kept, but must not disclose a home path.
    for member in ('.PKGINFO', '.BUILDINFO'):
        metadata = subprocess.run(['bsdtar', '-xOf', str(packages[0]), member], env=env,
                                  check=True, capture_output=True).stdout
        if re.search(rb'/(?:home|Users|root)(?:/|\s|$)', metadata):
            raise ValueError(f'personal path in native package metadata: {member}')
    payload = out / 'payload'
    payload.mkdir()
    # Scan the final archive payload as well as package(), after makepkg's hooks.
    run(['bsdtar', '-xf', str(packages[0]), '-C', str(payload), '--exclude', '.PKGINFO',
         '--exclude', '.BUILDINFO', '--exclude', '.MTREE'])
    run([sys.executable, '-I', '-B', str(source / 'packaging/linux/scan_package_linux.py'), str(payload)], 'scan.txt')
    digest = sha256(packages[0])
    packages[0].with_suffix(packages[0].suffix + '.sha256').write_text(f'{digest}  {packages[0].name}\n', encoding='utf-8')
    print(f'Built and scanned: {packages[0]}\nSHA-256: {digest}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as e:
        sys.exit(f'Arch build failed: {e}. See the build directory logs if preparation started.')
