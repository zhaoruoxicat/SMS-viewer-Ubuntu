#!/usr/bin/env python3
"""Build a native-dependency .deb without root access or a virtual environment."""

import argparse
import ast
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
PACKAGE = 'sms-forward-client'


def version():
    tree = ast.parse((ROOT / 'sms_client/__init__.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == '__version__' for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, str) and all(c.isdigit() or c == '.' for c in value):
                return value
    raise ValueError('sms_client/__init__.py 未定义有效版本号。')


def write(path, value, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8')
    path.chmod(0o755 if executable else 0o644)


def build(output):
    if shutil.which('dpkg-deb') is None:
        raise ValueError('缺少 dpkg-deb，请安装 dpkg 软件包。')
    release = version()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = f'{PACKAGE}_{release}_all.deb'
    with tempfile.TemporaryDirectory(prefix='.deb-build-', dir=output) as directory:
        temporary = Path(directory)
        staging = temporary / 'package'
        application = staging / 'usr/share' / PACKAGE
        for source in sorted((ROOT / 'sms_client').glob('*.py')):
            target = application / 'sms_client' / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copyfile(ROOT / 'logo.png', application / 'logo.png')
        icons = staging / 'usr/share/pixmaps'
        icons.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'logo.png', icons / f'{PACKAGE}.png')
        write(staging / 'usr/bin' / PACKAGE, '''#!/bin/sh
set -eu
cd /usr/share/sms-forward-client
export PYTHONDONTWRITEBYTECODE=1
exec /usr/bin/python3 -m sms_client "$@"
''', executable=True)
        write(staging / 'usr/share/applications' / f'{PACKAGE}.desktop', '''[Desktop Entry]
Version=1.0
Type=Application
Name=短信会话
Name[en]=SMS Forward Client
Comment=查看服务器短信并复制验证码
Exec=sms-forward-client
Icon=/usr/share/pixmaps/sms-forward-client.png
Terminal=false
Categories=Network;
StartupNotify=true
''')
        docs = staging / 'usr/share/doc' / PACKAGE
        docs.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'README.md', docs / 'README.md')
        changelog = (f'{PACKAGE} ({release}) unstable; urgency=medium\n\n'
                     '  * Remove transparent window margins and use a narrower opaque layout.\n\n'
                     ' -- SMS Forward Client <noreply@example.invalid>  Sat, 10 Oct 2026 00:00:00 +0800\n')
        (docs / 'changelog.gz').write_bytes(gzip.compress(changelog.encode(), mtime=0))
        payload = sorted(path for path in staging.rglob('*') if path.is_file())
        installed_size = sum((path.stat().st_size + 1023) // 1024 for path in payload)
        write(staging / 'DEBIAN/control', f'''Package: {PACKAGE}
Version: {release}
Section: net
Priority: optional
Architecture: all
Maintainer: SMS Forward Client <noreply@example.invalid>
Installed-Size: {installed_size}
Depends: python3 (>= 3.10), python3-pyside6.qtcore (>= 6.6), python3-pyside6.qtgui (>= 6.6), python3-pyside6.qtwidgets (>= 6.6), python3-pyside6.qtnetwork (>= 6.6)
Recommends: fonts-noto-cjk, qt6-wayland
Description: Desktop SMS viewer for a PHP forwarding server
 Displays the newest SMS records from a Token-authenticated PHP API.
 Includes automatic refresh, highlighted verification codes, clipboard
 actions, clickable hyperlinks and persistent per-user settings.
''')
        md5sums = ''.join(f'{hashlib.md5(path.read_bytes()).hexdigest()}  '
                          f'{path.relative_to(staging).as_posix()}\n' for path in payload)
        write(staging / 'DEBIAN/md5sums', md5sums)
        for path in staging.rglob('*'):
            if path.is_dir():
                path.chmod(0o755)
            elif path != staging / 'usr/bin' / PACKAGE:
                path.chmod(0o644)
        staging.chmod(0o755)
        environment = dict(os.environ)
        # Use stable source mtimes by default; callers may pin SOURCE_DATE_EPOCH.
        environment.setdefault('SOURCE_DATE_EPOCH', str(int(max(
            path.stat().st_mtime for path in [ROOT / 'build_deb.py', ROOT / 'README.md', ROOT / 'logo.png',
                                            *(ROOT / 'sms_client').glob('*.py')]))))
        artifact = temporary / name
        subprocess.run(['dpkg-deb', '--root-owner-group', '-Zxz', '-z9',
                        '--build', str(staging), str(artifact)], check=True, env=environment)
        destination = output / name
        os.replace(artifact, destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    write(output / 'SHA256SUMS', f'{digest}  {name}\n')
    print(f'已生成：{destination}')
    print(f'安装命令：sudo apt install {destination}')
    return destination


def main():
    parser = argparse.ArgumentParser(description='构建短信客户端 Debian 安装包')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    try:
        build(args.output_dir)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'打包失败：{exc}\n')


if __name__ == '__main__':
    main()
