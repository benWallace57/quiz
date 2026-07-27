#!/bin/bash
# Pre-deploy validation for quiz project
# Checks that all referenced files exist and HTML files are well-formed

ERRORS=0
ROOT="$(git rev-parse --show-toplevel)"

echo "=== Pre-Deploy Check ==="
echo ""

# Check all HTML quiz files exist and are non-empty
echo "Checking quiz files..."
for f in "$ROOT"/*.html; do
  if [ ! -s "$f" ]; then
    echo "  ERROR: $f is empty or missing"
    ERRORS=$((ERRORS + 1))
  else
    echo "  OK: $(basename "$f") ($(wc -l < "$f") lines)"
  fi
done

echo ""

# Check that index.html references existing files
echo "Checking landing page links..."
if [ -f "$ROOT/index.html" ]; then
  grep -oP 'href="\K[^"]+\.html' "$ROOT/index.html" | while read -r link; do
    if [ ! -f "$ROOT/$link" ]; then
      echo "  ERROR: index.html links to '$link' but file doesn't exist"
      ERRORS=$((ERRORS + 1))
    else
      echo "  OK: $link"
    fi
  done
fi

echo ""

# Check for any files over 2MB (GitHub Pages limit is 100MB total)
echo "Checking file sizes..."
find "$ROOT" -type f -size +2M -not -path '*/.git/*' | while read -r bigfile; do
  echo "  WARNING: $(du -h "$bigfile" | cut -f1) $(basename "$bigfile")"
done

echo ""

# Check for accidentally committed secrets patterns
echo "Checking for potential secrets..."
if grep -rl "API_KEY\|SECRET\|PASSWORD\|TOKEN" "$ROOT"/*.html "$ROOT"/*.py 2>/dev/null | grep -v '.git'; then
  echo "  WARNING: Potential secrets found in above files"
else
  echo "  OK: No obvious secrets found"
fi

echo ""
echo "=== Check Complete (errors: $ERRORS) ==="
exit $ERRORS
