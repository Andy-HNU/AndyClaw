#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <target> <file-path> <caption>"
  exit 1
fi

TARGET="$1"
FILE_PATH="$2"
CAPTION="$3"

if [[ ! -f "$FILE_PATH" ]]; then
  echo "File not found: $FILE_PATH"
  exit 2
fi

openclaw message send \
  --channel telegram \
  --target "$TARGET" \
  --media "$FILE_PATH" \
  --message "$CAPTION"
