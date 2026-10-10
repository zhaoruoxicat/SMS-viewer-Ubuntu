#!/usr/bin/env bash
set -euo pipefail

sms_client_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
sms_client_applications="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

python3 - "$sms_client_dir" "$sms_client_applications" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
destination = Path(sys.argv[2])

def exec_quote(value):
    # Desktop-entry values have one escape layer in addition to Exec quoting.
    value = str(value)
    if '\n' in value or '\r' in value:
        raise SystemExit('安装目录不能包含换行。')
    for char in ('\\', '"', '`', '$'):
        value = value.replace(char, '\\' + char)
    return '"' + value.replace('\\', '\\\\') + '"'

def value_escape(value):
    return str(value).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')

destination.mkdir(parents=True, exist_ok=True)
entry = destination / 'sms-forward-client.desktop'
entry.write_text(
    '[Desktop Entry]\n'
    'Version=1.0\n'
    'Type=Application\n'
    'Name=短信会话\n'
    'Name[en]=SMS Forward Client\n'
    'Comment=查看服务器短信并复制验证码\n'
    f'Exec={exec_quote(root / "run.sh")}\n'
    f'Icon={value_escape(root / "logo.png")}\n'
    'Terminal=false\n'
    'Categories=Network;\n'
    'StartupNotify=true\n', encoding='utf-8')
entry.chmod(0o644)
print(f'已添加应用菜单快捷方式：{entry}')
print('可在 Ubuntu 应用菜单搜索“短信会话”。项目移动后请重新执行本脚本。')
PY
