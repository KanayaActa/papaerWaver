#!/bin/bash

# エラー時は即終了
env_error() {
  echo "[エラー] Python仮想環境の作成や依存パッケージのインストールに失敗しました。"
  exit 1
}
set -e

# プロジェクトルートから実行することを推奨
SCRIPT_DIR=$(cd $(dirname $0); pwd)
cd "$SCRIPT_DIR"

# バックエンドセットアップ
echo "=== バックエンドセットアップ ==="
cd backend || env_error
python3 -m venv venv || env_error
source venv/bin/activate || env_error
pip install -r requirements.txt || env_error

# バックエンド起動（バックグラウンド）
echo "=== バックエンド起動 ==="
python app.py &
BACKEND_PID=$!

cd "$SCRIPT_DIR"

# フロントエンドセットアップ
cd frontend || env_error
echo "=== フロントエンドセットアップ ==="
pnpm install

# フロントエンド起動（バックグラウンド）
echo "=== フロントエンド起動 ==="
pnpm dev &
FRONTEND_PID=$!

cd "$SCRIPT_DIR"

echo "=== 起動完了 ==="
echo "バックエンド: http://localhost:5001"
echo "フロントエンド: http://localhost:5173"
echo "終了するには 'kill $BACKEND_PID $FRONTEND_PID' を実行してください。" 