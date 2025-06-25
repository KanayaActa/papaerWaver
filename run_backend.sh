#!/bin/bash

set -e

cd "$(dirname "$0")/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# main.pyの場所を確認して実行
if [ -f src/main.py ]; then
  echo "=== バックエンド起動: src/main.py ==="
  python src/main.py
else
  echo "[エラー] src/main.py が見つかりません。backend/src/ ディレクトリを確認してください。"
  exit 1
fi 