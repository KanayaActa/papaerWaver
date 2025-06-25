#!/bin/bash

set -e

cd "$(dirname "$0")/frontend"
pnpm install

echo "=== フロントエンド起動 ==="
pnpm dev 