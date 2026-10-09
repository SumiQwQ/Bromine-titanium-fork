#!/usr/bin/env bash
# Bromine rebrand step. Run from anywhere inside your Titanium fork, BEFORE the build/patch step.
#   bash bromine/scripts/rebrand.sh --dry-run   # list what would change
#   bash bromine/scripts/rebrand.sh             # apply (review with `git diff` afterwards)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# shellcheck source=../bromine.conf
source "$HERE/../bromine.conf"
export BROMINE_NAME BROMINE_PACKAGE OLD_PACKAGE

BROMINE_DIR="${HERE%/scripts}"
BROMINE_REL="${BROMINE_DIR#"$ROOT"/}"

DRY=0
[[ "${1:-}" == "--dry-run" ]] && DRY=1

if [[ "$BROMINE_PACKAGE" == *CHANGEME* ]]; then
  if (( DRY )); then
    echo "warning: BROMINE_PACKAGE in bromine.conf is still a placeholder" >&2
  else
    echo "error: set BROMINE_PACKAGE in bromine.conf first" >&2
    exit 1
  fi
fi

pkg_re="${OLD_PACKAGE//./\\.}"
pattern="${pkg_re}|Titanium(?! Extension)"

count=0
while IFS= read -r -d '' f; do
  case "$f" in
    README.md|LICENSE*|COPYING*|"$BROMINE_REL"/*) continue ;;
  esac
  [[ -f "$f" ]] || continue              # skips submodules (e.g. vanadium) and deleted files
  grep -Iq . "$f" || continue            # skips binary and empty files
  grep -qP "$pattern" "$f" || continue

  count=$((count + 1))
  if (( DRY )); then
    echo "would change: $f"
  else
    perl -pi -e 's/\Q$ENV{OLD_PACKAGE}\E/$ENV{BROMINE_PACKAGE}/g; s/Titanium(?! Extension)/$ENV{BROMINE_NAME}/g' "$f"
    echo "changed: $f"
  fi
done < <(git ls-files -z)

echo "text files changed (or that would change): $count"

# Launcher icons
if python3 -c 'import PIL' 2>/dev/null; then
  if (( DRY )); then
    python3 "$HERE/make_icons.py" apply "$ROOT" --dry-run
  else
    python3 "$HERE/make_icons.py" apply "$ROOT"
  fi
else
  echo "warning: Pillow not installed (pip install pillow); skipping icons" >&2
fi

if (( ! DRY )); then
  echo
  echo "Done. Review with: git diff --stat"
  echo "Remaining mentions (expected: README, LICENSE, URLs):"
  git grep -n -I "Titanium" -- . ":!$BROMINE_REL" | head -20 || true
fi
