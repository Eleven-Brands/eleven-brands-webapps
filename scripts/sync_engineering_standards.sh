#!/usr/bin/env bash
set -euo pipefail

STANDARDS_REPO="${STANDARDS_REPO:-Eleven-Brands/eleven-brands-engineering-standards}"
STANDARDS_REF="${STANDARDS_REF:-main}"

echo "Syncing engineering standards from ${STANDARDS_REPO}@${STANDARDS_REF}"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

git clone \
  --depth 1 \
  --branch "$STANDARDS_REF" \
  "https://x-access-token:${GITHUB_TOKEN}@github.com/${STANDARDS_REPO}.git" \
  "$tmp_dir/standards"

# ---- Copy Markdown standards files ----
cp -f "$tmp_dir/standards/CODE_OF_CONDUCT.md" .
cp -f "$tmp_dir/standards/CONTRIBUTING.md" .
cp -f "$tmp_dir/standards/LICENSE" .
cp -f "$tmp_dir/standards/setup_gcp.md" .
cp -f "$tmp_dir/standards/setup_local_development.md" .

# ---- Enforce .github conventions (mandatory) ----
rm -rf .github
mkdir -p .github
rsync -a "$tmp_dir/standards/.github/" .github/

echo "Sync complete."
