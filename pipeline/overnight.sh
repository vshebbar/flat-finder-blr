#!/bin/zsh
# Unattended: finish brochures, read HRERA filings, rebuild, test, deploy.
cd "${0:A:h}"
OCR=(uv run -q --with pyobjc-framework-Vision --with pyobjc-framework-Quartz python)
while pgrep -f "brochure_ocr.py gurgaon" >/dev/null; do sleep 60; done
$OCR brochure_ocr.py gurgaon >> cache_brochures.log 2>&1      # resumes any left
$OCR hrera.py gurgaon > cache_hrera.log 2>&1
/opt/homebrew/bin/python3 build_city.py gurgaon > cache_build.log 2>&1 || exit 1
cd ../web && npx vitest run --root .. cli web/src > ../pipeline/cache_tests.log 2>&1 || exit 1
npm run build >/dev/null 2>&1 || exit 1
cd .. && git add -A && git -c user.email=126209124+kairothq@users.noreply.github.com commit -qm "Overnight: brochure and HRERA plan readings, phone search and photo fixes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q
cd web && npx --yes wrangler@4 pages deploy dist --project-name flat-finder --branch main --commit-dirty=true > ../pipeline/cache_deploy.log 2>&1
echo done > ../pipeline/cache_overnight.done
