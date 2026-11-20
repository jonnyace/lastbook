"""Distro-neutral /opt and desktop layout, shared by Debian and Arch builds.

Inputs are explicitly prepared ship assets, installed wheels and the compiled
lastbooksrc plugin. Never copy a checkout, data folder, or cache wholesale.
The caller must run scan_package_linux.py on the result before packaging it.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

PROGRAM_FILES = (
    'app/main.py', 'app/bridge.py', 'app/shell_linux.py',
    'server.py', 'retrieval.py', 'assistant.py', 'llm_local.py',
    'engine/__init__.py', 'engine/paths.py', 'engine/library.py',
    'engine/saved_pages.py', 'engine/address_search.py', 'engine/update.py',
    'engine/encyclopedias.py', 'engine/safe_paths.py', 'engine/page_tables.py',
    'engine/setup/__init__.py', 'engine/setup/api.py', 'engine/setup/download.py',
    'engine/setup/hardware.py', 'engine/setup/install.py', 'engine/setup/manifest.py',
    'engine/setup/roots.pem',
)
ASSETS = ('packaging/linux/lastbook.py', 'packaging/linux/lastbook.desktop', 'packaging/icon/tile-1024.png')


def checked(path, directory=False):
    """Do not follow symlinks, including symlinked ancestors, into other inputs."""
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f'symlink input refused: {path}')
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError(f'missing required {"directory" if directory else "file"}: {path}')
    return path


def tree_files(root):
    root = checked(root, directory=True)
    files = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f'symlink or special file refused: {path}')
        if path.is_file():
            files.append(path.relative_to(root))
    return files


def copy_file(source, dest):
    source = checked(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)


def vendor_kept(rel):
    # Same exclusions as the original Debian wheel installation.
    return not (rel.parts[0] in {'bin', 'pypdfium2_cli'}
                or any(p in {'tests', 'testing', '__pycache__'} for p in rel.parts)
                or rel.parts[:2] == ('numpy', 'f2py') or '_tests' in rel.name)


CHANNELS = ('deb', 'arch')     # how the package is installed and updated; engine/update.py reads opt/lastbook/CHANNEL


def stage(source, ship, vendor, plugin, dest, version, llm=None, channel='deb'):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+~_-]*', version):
        raise ValueError('invalid package version')
    if channel not in CHANNELS:
        raise ValueError(f'unknown package channel {channel!r}; expected one of {", ".join(CHANNELS)}')
    source, ship, vendor = (checked(p, directory=True) for p in (source, ship, vendor))
    plugin = checked(plugin)
    dest = Path(os.path.abspath(dest))
    if any(p.is_symlink() for p in (dest, *dest.parents)):
        raise ValueError('stage must not contain symlink ancestors')
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise ValueError('stage must be absent or empty; refusing to overwrite it')
    # The checkout is read by explicit filenames only, so Debian's existing
    # derived/app-build output may safely live inside it. Copied input trees
    # must remain disjoint from the destination to prevent recursive staging.
    if dest == source or dest in source.parents:
        raise ValueError('stage must not contain its source checkout')
    for path in (ship, vendor, plugin, *([llm] if llm else [])):
        path = Path(path).resolve()
        if dest == path or dest in path.parents or path in dest.parents:
            raise ValueError('stage must not overlap its inputs')
    # Validate all inputs before writing anything. Optional runner files retain
    # Debian's selection and executability; no runner is required by Arch.
    for rel in (*PROGRAM_FILES, *ASSETS):
        checked(source / rel)
    checked(ship / 'web/index.html')
    checked(ship / 'content/gaps.json')
    checked(ship / 'setup/manifest-v1.json')
    trees = [(ship / name, Path(name), tree_files(ship / name)) for name in ('web', 'content')]
    trees.append((vendor, Path('lib'), [p for p in tree_files(vendor) if vendor_kept(p)]))
    runner_copies = []
    if llm:
        llm = checked(llm, directory=True)
        runner = (llm / 'lastbook-llm').resolve()
        if not runner.is_relative_to(llm):
            raise ValueError('runner symlink escapes its directory')
        checked(runner)
        if not os.access(llm / 'lastbook-llm', os.X_OK):
            raise ValueError('local AI runner must be executable')
        runner_files = [Path('lastbook-llm')]
        runner_files += [p.relative_to(llm) for pattern in ('*.so*', 'LICENSE*', 'NOTICE*') for p in sorted(llm.glob(pattern))]
        for rel in runner_files:
            resolved = (llm / rel).resolve()
            if not resolved.is_relative_to(llm):
                raise ValueError(f'runner symlink escapes its directory: {rel}')
            runner_copies.append((checked(resolved), rel))
    opt = dest / 'opt/lastbook'
    for rel in PROGRAM_FILES:
        copy_file(source / rel, opt / rel)
    for src, target, files in trees:
        for rel in files:
            copy_file(src / rel, opt / target / rel)
    for src, rel in runner_copies:
        copy_file(src, opt / 'llm' / rel)
    copy_file(ship / 'setup/manifest-v1.json', opt / 'setup/manifest-v1.json')
    copy_file(source / 'packaging/linux/lastbook.py', opt / 'lastbook.py')
    copy_file(plugin, opt / 'gst/libgstlastbooksrc.so')
    (opt / 'VERSION').write_text(version + '\n', encoding='utf-8')
    (opt / 'CHANNEL').write_text(channel + '\n', encoding='utf-8')
    launcher = dest / 'usr/bin/lastbook'
    launcher.parent.mkdir(parents=True)
    launcher.write_text('#!/bin/sh\nexec /usr/bin/python3 -I -B /opt/lastbook/lastbook.py "$@"\n', encoding='utf-8')
    launcher.chmod(0o755)
    copy_file(source / 'packaging/linux/lastbook.desktop', dest / 'usr/share/applications/lastbook.desktop')
    from PIL import Image
    with Image.open(source / 'packaging/icon/tile-1024.png') as image:
        image = image.convert('RGBA')
        for n in (16, 24, 32, 48, 64, 128, 256, 512):
            directory = dest / f'usr/share/icons/hicolor/{n}x{n}/apps'
            directory.mkdir(parents=True, exist_ok=True)
            image.resize((n, n), Image.Resampling.LANCZOS).save(directory / 'lastbook.png', optimize=True)
    doc = dest / 'usr/share/doc/lastbook/copyright'
    doc.parent.mkdir(parents=True)
    doc.write_text("Lastbook: MIT licence, https://github.com/Immortal-Protocols/lastbook\n"
                   "Bundled Python packages in /opt/lastbook/lib keep their own licences (see each *.dist-info). The local AI's runner in /opt/lastbook/llm:\n"
                   "llama.cpp, MIT licence (LICENSE-llama.cpp.txt there).\n", encoding='utf-8')
    # Serial compilation avoids multiprocessing's local socket and gives the
    # same bytecode paths under /opt regardless of the build directory.
    subprocess.run([sys.executable, '-I', '-m', 'compileall', '-q', '-j', '1', '-s', str(dest), '-p', '/', str(opt)], check=True)
    for path in [dest, *dest.rglob('*')]:
        path.chmod(0o755 if path.is_dir() else (path.stat().st_mode & 0o777 & ~0o022) | 0o444)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'ship', 'vendor', 'plugin', 'stage'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--version', required=True)
    ap.add_argument('--channel', choices=CHANNELS, default='deb')
    ap.add_argument('--llm', type=Path)
    a = ap.parse_args()
    stage(a.source, a.ship, a.vendor, a.plugin, a.stage, a.version, a.llm, a.channel)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        sys.exit(f'Staging failed: {e}')
