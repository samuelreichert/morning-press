# Contributing

Use synthetic data for every fixture and bug report. Do not submit a reader's profile, edition, calendar export, or screenshot containing account details.

Use Python 3.10+, install `requirements.txt` in an isolated environment, and run:

```bash
python -m unittest discover -s tests -v
python skills/morning-press/scripts/press.py --data-dir /private/test-location demo
python skills/morning-press/scripts/press.py --data-dir /private/test-location demo --qr
```

For renderer changes, render both PDFs to images and review every page. Link and margin checks do not prove a readable design. Decode printed QR samples after changing QR code generation or sizing. Do not check generated output into Git.

Keep `SKILL.md` focused on routing and operational requirements. Put interview, editorial, and provider-specific details in their existing references. Keep the installed skill folder self-contained; repository-level docs are for maintainers.

Schema changes need a versioning/migration decision. Never silently change the meaning of an existing reader's preferences. New optional sections must remain optional and source-backed. Integrations need documented actual capabilities and failure behavior; a menu entry is not proof of provider support.

Before committing, stage only intended files, update `public-files.json` if needed, run `python tools/check_public.py --history`, and inspect `git diff --cached`. A CI pass is not a substitute for checking prose for personal information.
