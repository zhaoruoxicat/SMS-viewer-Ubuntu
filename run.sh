#!/usr/bin/env bash
set -euo pipefail

sms_client_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$sms_client_dir"

if [[ -n "${SMS_CLIENT_PYTHON:-}" ]]; then
    sms_client_python="$SMS_CLIENT_PYTHON"
elif [[ -x "$sms_client_dir/.venv/bin/python" ]]; then
    sms_client_python="$sms_client_dir/.venv/bin/python"
else
    sms_client_python="python3"
fi

if ! "$sms_client_python" -c 'from PySide6 import QtCore, QtGui, QtWidgets, QtNetwork' >/dev/null 2>&1; then
    cat >&2 <<'MESSAGE'
缺少 PySide6 运行依赖。请在本目录执行：
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
然后重新运行 ./run.sh。
如果无法创建虚拟环境，先执行 sudo apt install python3-venv。
MESSAGE
    exit 1
fi

exec "$sms_client_python" -m sms_client "$@"
