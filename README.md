# Morning Press

Your morning newspaper, shaped by your interests.

Morning Press is an open source agent skill with guided setup and a local PDF/Markdown renderer. Choose your regions, topics, title, sections, page count, weather units, recommendation tastes, and link preferences. Keep your reader profile and generated editions outside the public package.

No calendar, market table, coding section, or home city is mandatory. You can create a small news briefing, a local culture newspaper, a reading companion, or your own combination.

## Start in Codex

Ask the built-in installer to install the skill from this repository:

```text
Use $skill-installer to install skills/morning-press from
https://github.com/samuelreichert/morning-press
```

Then ask:

```text
Use $morning-press to set up my newspaper. Ask me a few questions at a time.
```

The interview runs in your preferred language; this repository's English documentation does not force English output. After setup, ask:

```text
Use $morning-press to create today's edition with my main profile.
```

The skill installer installs the skill folder, including its scripts, schemas, and fictional example. To render files, the host also needs Python 3.10+ and the dependencies below. A host with a suitable bundled runtime can use it. The root `plugin.json` also packages the skill with an onboarding entrypoint; this repository is not a claim of acceptance into a plugin directory.

Local discovery and distribution guidance: [OpenAI skills documentation](https://learn.chatgpt.com/docs/build-skills) and [plugin packaging](https://developers.openai.com/plugins/build/plugins).

## Try the terminal demo

```bash
git clone https://github.com/samuelreichert/morning-press.git
cd morning-press
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python skills/morning-press/scripts/press.py demo
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

The demo produces a two-page fictional PDF, Markdown, layout validation, and editorial JSON. Every PDF page is labeled **DEMONSTRATION**. It needs no account, network research, or personal setup. To compare printed QR codes:

```bash
.venv/bin/python skills/morning-press/scripts/press.py demo --qr
```

Output is printed to the terminal and saved under the private data location, never the repository. Existing editions are preserved in revision folders.

For a terminal setup instead of a conversational interview:

```bash
.venv/bin/python skills/morning-press/scripts/press.py --profile main setup
```

## What setup covers

| Area | Choices |
| --- | --- |
| Identity | Title, subtitle, newspaper language, timezone |
| Reading | PDF, Markdown, both; 1-12 PDF pages; A4/Letter; color/monochrome; 10-13 pt body text |
| News | Cities, regions, countries, worldwide coverage, themes, depth, source restrictions, exclusions |
| Weather | Optional; several places, local timezones, Celsius/Fahrenheit, wind units, compact/detailed |
| Agenda | Optional; manual input or preferred provider; calendars to include; details or busy-only |
| Economy | Optional; selected instruments, currency pairs, macroeconomic topics, reporting currency |
| Recommendations | Optional books/films/series; tastes, dislikes, already-read/watched items, spoilers, streaming country/services |
| Other sections | Events, weekend ideas, learning, positive news, language practice, custom categories |
| Links | Clickable PDF headlines and printed QR codes, independently selectable |
| Routine | Local time and weekday preferences; scheduling and printing require separate requested actions |

The terminal wizard supports one section per kind and one calendar source. Conversational setup and the schema support multiple news/custom sections and calendar preferences. Checkpoints remain drafts until you review and confirm. Later preference changes preserve unrelated choices.

New reader profiles start empty. No newspaper language, location, interests, sections, source policy, currency, page count, link choice, or routine is preselected. Required choices need an explicit answer; optional answers may stay empty. Only the selected reader's previous answers are retained when resuming. The demo has its own synthetic profile and never supplies onboarding defaults. No author preferences or personal information may be reused, including as examples or inferred editorial rules.

## What runs where

```text
Public package             Private data (outside the package)
  skill + interview          profiles/main/profile.json
  schemas + renderer         profiles/main/drafts/
  fictional examples         profiles/main/issues/YYYY-MM-DD/
  tests + documentation      profiles/sample/demos/
```

The default data root is `~/.local/share/morning-press` (or `$XDG_DATA_HOME/morning-press`). Override it with `MORNING_PRESS_HOME` or a global `--data-dir /private/location` option before the subcommand. Keep that location out of any public repository. Profiles are stored as separate names; no telemetry or credential store is included.

The **host agent** researches current sources and uses available authorized connectors. The **local scripts** validate the profile and editorial JSON and render files. The scripts do not fetch news, connect accounts, install integrations, schedule, print, or send messages. A skill is not a standalone unattended news service.

Google, Apple, Outlook, Notion, and ICS are setup preferences with documented host/manual paths, not bundled native integrations. A requested provider may remain unavailable. See [integration behavior](skills/morning-press/references/integrations.md).

## Produce and review an edition

```bash
# Create a private collection draft after setup.
.venv/bin/python skills/morning-press/scripts/press.py --profile main brief

# The host agent researches enabled sections and edits the returned draft.
.venv/bin/python skills/morning-press/scripts/press.py --profile main validate --issue /private/location/draft.json
.venv/bin/python skills/morning-press/scripts/press.py --profile main render /private/location/draft.json
```

Every real non-calendar item requires source provenance. Disabled sections are rejected. Unavailable sources remain explicitly unavailable. PDF page count must match the selected budget; the renderer fails rather than silently truncating or shrinking type. Markdown has no fixed page count. The output includes `layout.json` with page, margin, and PDF-link checks; a human/agent must still inspect rendered PDF pages before delivery.

The first renderer is a simple two-column editorial template with text-based weather and economy. It supports Latin text covered by its embedded font; unsupported scripts fail clearly and can use Markdown. It does not yet include the original private newspaper's photography, market tables, or puzzle engine. See [implementation and roadmap](docs/PLAN.md).

## Contribute safely

Run tests and the public-file guard before publishing:

```bash
.venv/bin/python -m unittest discover -s tests -v
git add -- public-files.json README.md LICENSE CONTRIBUTING.md requirements.txt plugin.json .gitignore .github docs skills tests tools
.venv/bin/python tools/check_public.py --history
```

The guard examines indexed file contents and every reachable historical blob against an explicit public-file manifest and common sensitive-data patterns. The manifest separates current `files` from reviewed `historical_files` retained after renames; historical content is still scanned. It is a useful check, not proof that arbitrary prose is anonymous. Review every staged diff. Do not attach a real edition or profile to an issue or PR. See [privacy](docs/PRIVACY.md) and [contributing](CONTRIBUTING.md).

MIT licensed. Article text, photos, publisher content, and account data are not relicensed by this code's license.
