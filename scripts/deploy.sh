#!/usr/bin/env bash
# One-shot first publish. Usage: scripts/deploy.sh [github-user] [repo-name]
set -euo pipefail
USER="${1:-mfenickfau}"; REPO="${2:-econ-dashboards}"
cd "$(dirname "$0")/.."
python3 scripts/fetch_fred.py
[ -d .git ] || git init -b main
git add .
git commit -m "Evergreen econ dashboards" || true
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$USER/$REPO.git"
git push -u origin main
echo "Now enable Settings -> Pages -> Source: GitHub Actions in https://github.com/$USER/$REPO/settings/pages"
echo "Site: https://$USER.github.io/$REPO/"
