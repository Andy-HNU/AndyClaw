#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-.}"
OUT_DIR="${2:-./security-scan-out}"
mkdir -p "$OUT_DIR"

echo "[ecc] scanning: $TARGET_DIR"

# Secret-like patterns (best-effort, may include false positives)
grep -RInE --exclude-dir=.git --exclude='*.png' --exclude='*.jpg' --exclude='*.svg' \
  'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----|api[_-]?[Kk]ey[[:space:]]*[:=]|secret[[:space:]]*[:=]|token[[:space:]]*[:=]' \
  "$TARGET_DIR" > "$OUT_DIR/secret-scan.txt" || true

# Dangerous execution patterns
grep -RInE --exclude-dir=.git \
  'curl[[:space:]].*\|[[:space:]]*(bash|sh)|wget[[:space:]].*\|[[:space:]]*(bash|sh)|bash[[:space:]]+-i[[:space:]]+>&[[:space:]]+/dev/tcp|nc[[:space:]]+-e[[:space:]]+/bin/(sh|bash)|base64[[:space:]]+-d[[:space:]]*\|[[:space:]]*(bash|sh)|subprocess\.(Popen|run)\(.*shell[[:space:]]*=[[:space:]]*True|os\.system\(|child_process\.exec\(|new Function\(|eval\(' \
  "$TARGET_DIR" > "$OUT_DIR/danger-scan.txt" || true

cat <<MSG
[ecc] done
- $OUT_DIR/secret-scan.txt
- $OUT_DIR/danger-scan.txt
MSG
