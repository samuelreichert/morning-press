# Guided setup

Use the reader's conversation language. Documentation language does not set the newspaper language. Group questions into short rounds, prefill answers already given in this setup, and allow "skip", "no", and "change later". Do not connect services just to ask about them.

The setup is an interview, a private configuration, a review, and a preview. Do not ask one giant questionnaire or silently inherit the bundled example's interests. The example profile shows the JSON shape, not a recommended personal profile.

## Interview rounds

1. **Identity and reading experience.** Ask title, optional subtitle, newspaper language, and IANA timezone. Ask PDF, Markdown, or both; for PDF ask pages (1-12), A4/Letter, color/monochrome, body size (10-13 pt). Discuss a feasible scope if the chosen sections cannot fit. Ask clickable headlines and printed QR codes independently. QR is PDF-only; a Markdown-only reader can use regular links.
2. **Content menu.** Offer news, weather, calendar, economy, events, books, movies/series, learning, positive news, a language corner, and custom categories. Let the reader enable only what they want and order the sections. News can have separate local, national, world, or topic sections, each with a unique ID. Custom categories use `kind: custom` and ordinary sourced editorial items.
3. **Only the enabled branches.** Use the table below. Ask the maximum number of items and brief/balanced/deep coverage per section. A maximum is a cap, not a quota to fill with weak material.
4. **Editorial boundaries.** Ask preferred or excluded sources, excluded topics, audience, tone, news lookback, and repeat tolerance. `sources.mode: open` allows researched credible sources; `allowlist` restricts the section to the specified domains. Do not add an unapproved domain to an allowlist. Defaults can be suggested and accepted together; do not conceal them.
5. **Delivery and review.** Ask whether the reader is interested in a schedule or printing, and relevant local time/weekdays if so. These are preferences only. Summarize what is enabled, skipped, and still unavailable, plus local data location. Let the reader correct it, then confirm setup and save `status: ready`. Offer a clearly labeled fictional preview or proceed to an explicitly requested real edition.

| Enabled section | Follow-up questions |
| --- | --- |
| News / positive news | Which cities, regions, countries, or worldwide coverage? Which topics, depth, and source policy? Is a specific positive-news section wanted? |
| Weather | Which locations and each location's timezone? Celsius/Fahrenheit; wind km/h, mph, or m/s? Compact or detailed forecast? Detailed includes rain periods, wind/gusts, and available official warnings. |
| Calendar | Skip, manual input, or provider? Google, Apple, Outlook, Notion dated records, ICS, or another source? Which calendars and details vs busy-only? Discover available tools only after this choice. Never ask for a password or private feed URL in chat. |
| Economy | Markets, macroeconomics, or both? Which instruments, pairs, countries, and reporting currency? No mandatory crypto, exchange pair, or index. Put macro topics in `topics`, instruments in `options.instruments`. |
| Events | Which regions, themes, horizon (1-90 days), and optional weekend plan? Record budget/access needs in `topics` or `exclude` if relevant. |
| Books | Genres, themes, language preferences, favorite authors, disliked or already-read titles, and spoiler policy? Use `options.interests` and `options.avoid`. |
| Screen | Films, series, or both; genres and dislikes; spoiler policy; actual catalog country and services? No automatic streaming subscription assumptions. |
| Learning | Subject, level, concept/challenge/mixed? Coding is one possible subject, not a mandatory section. |
| Language | Which target language, proficiency, and practical context? |
| Custom | Name, purpose, topics, exclusions, region if relevant, source policy, depth, and item cap? |

## Persist and resume

Use `assets/profile.schema.json` as the source of truth for field names and enums. Save intermediate answers as `status: draft` in the private location with `press.py import-profile`; subsequent draft updates need `--replace`. Do not include tokens, account identifiers, email addresses, calendar subscription URLs, meeting links, or raw events. Calendar names are sufficient to express scope; the host stores authentication separately.

The terminal command `press.py setup` checkpoints section answers and resumes a draft. It supports one section per kind; use conversation or JSON for several news/custom sections or multiple calendars. For confirmed conversational choices, call `import-profile --confirm` with the full valid draft. Do not label a connector `connected` until a scoped read has actually succeeded.

On later edits, preserve unrelated choices. A complete profile still needs review when a change affects what will be read or published. Routine daily production should reuse that confirmed profile without asking the same setup questions again.
