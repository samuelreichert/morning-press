# Implementation and roadmap

## Product boundary

Ship a reusable newspaper skill, not a shared service holding readers' data. Keep editorial defaults configurable and avoid migration that implicitly reads a prior installation. The public project starts with a new Git history and synthetic fixtures. Private installations continue independently.

## Implemented in 0.1.1

1. A conditional conversational setup and a terminal alternative with empty new-reader profiles, explicit choices, draft checkpoints, review, confirmation, and later edits. Setup never loads the demo profile or inherits author information.
2. A versioned strict profile schema for identity, language/timezone, enabled sections, sources, regional coverage, recommendations, links, page budget, and delivery preferences.
3. Private, separate named profiles, outside-package path checks, restrictive new-file permissions where supported, and revision-preserving output.
4. A strict editorial data contract with unavailable/no-updates distinctions, public source provenance, canonical HTTPS links, section caps, and disabled-section rejection.
5. A portable PDF and Markdown renderer: two columns, embedded font, 1-12 requested pages, A4/Letter, independent clickable headlines/printed QR codes, geometry and real link checks.
6. A fully fictional demo, behavior tests, a public-file manifest and history-aware release guard, CI, MIT license, and contribution instructions.
7. Capability-based integration instructions: discover authorized host tools and use manual fallbacks honestly. Provider selection never claims a live connection.

The schemas and scripts are implemented. Research, interpretation of weather/market data, connector use, editorial selection, and visual review are responsibilities of the host agent following the skill. No live account, real-news pipeline, scheduler, or physical printer is tested by the synthetic suite.

## Acceptance scenarios

| Scenario | Expected result |
| --- | --- |
| New reader | Setup first; no other project's data is read |
| News only | No weather/calendar/economy calls; no empty boxes for those sections |
| Several regions | Per-section regions and unique IDs, no hardcoded home location |
| No calendar | No connector needed |
| Preferred calendar absent | Explicit unavailable state or accepted manual path |
| Fahrenheit + distant city | Local forecast date/timezone and chosen units in researched copy |
| Books and screen | Selected tastes, spoiler policy, exclusions, actual catalog country |
| QR on/off | Printable QR artwork only when selected; clickable headlines remain independent |
| Too much/too little content | Clear page-budget failure; no silent truncation or filler |
| Profile incomplete | Real production blocked; fictional demo still available |
| Revised edition | Previous output retained with same edition number for that date |
| Release | Only reviewed public files, no private data or inherited history |

## Next improvements

Prioritize these after real feedback; no provider-specific support is implied by this list.

- Polished additional templates, optional licensed photography, dedicated weather/market tables, and accessible larger-type layouts.
- Validated optional puzzles with unique-solution and print-size checks.
- Additional font packs and writing systems with explicit licenses and visual tests.
- A separately tested ICS adapter for recurrence, exceptions, all-day dates, and DST; explicit host-specific connector recipes.
- Optional verified scheduling recipes per host, with failure handling and quiet unchanged-state behavior.
- More complete locale formatting and optional structured weather/market fields, while keeping provenance and missing-data semantics.
- A broader host compatibility matrix and behavioral evaluations of interviews in several languages.

Do not solve these by copying personal state or embedding one reader's preferences into the public skill.
