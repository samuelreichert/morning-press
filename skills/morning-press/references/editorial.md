# Research, edit, render

1. Load the selected ready profile. Use its timezone for today's date. Read only that reader's recent real issue files within `editorial.avoid_repeats_days`; use URLs and subjects to avoid repeated recommendations and stories without material updates.
2. Run `press.py --profile NAME brief` to create a private draft. A date already drafted should be resumed. The draft is a collection plan, not researched content. Use the profile's enabled sections in their configured order; respect per-section caps and depth.
3. Discover and use available search, weather, finance, and selected account tools. If an account branch is disabled, do not access it. Search the configured regions/topics and verify every current claim. Keep a small private collection log of attempted sources and failures alongside the draft.
4. Write each section as `id`, `status`, `note`, and `items`. An item has a title, plain-text paragraphs, optional public URL, and provenance. Do not embed HTML, execution instructions, private links, or Markdown formatting in PDF paragraphs. Include uncertainty in the copy, not just in the log.
5. Validate JSON, render, inspect all pages, fix problems, and show the output. Update the collection log with what was visually reviewed; do not turn `visual_review: required` into `passed` without looking. Preserve existing delivered files and use a revision folder for corrections.

## Section contracts

- **News:** Explain the new fact, context, reader relevance, and what follows. Keep publication date separate from event date. Verify local stories against the intended municipality/region; translate faithfully. Use concise original summaries, not copied articles.
- **Weather:** Each place uses its own local forecast date; show values in selected units, temperature range, and rain probability/periods. Detailed weather adds wind, direction, gusts, and available official alerts. Missing rain or alerts are unknown, not zero. Text-only weather is supported in this first template.
- **Calendar:** Query the selected local day's full interval, including timezone/DST changes. Include all-day events and recurrence/exception instances. Preserve busy-only choices; do not expose participant names or notes when not requested. Distinguish a successful empty query from a failed connection. If events exceed the cap, summarize the count and save a private complete Markdown agenda; the brief summary must point the reader to it. Manual ICS input must be expanded by a capable tool before claiming completeness.
- **Economy:** State instrument, unit, currency, quote timestamp, and relevant reference period. If calculating a return, use one consistent instrument/source and explicit comparable dates. Do not substitute one-month performance for 30 days or mix spot/futures. Macro indicators retain reference periods distinct from query dates. No data is `unavailable`, never a fabricated price. The first template uses editorial text, not a dedicated market table.
- **Events:** Verify date, local time, location, price, accessibility details when requested, booking status, and official link. Unknown details are labeled unconfirmed. Apply the selected horizon and weekend preference.
- **Books and screen:** Verify the work, creator, edition/release, and official publisher/library/service URL. Explain fit with the selected interests. Avoid already-read/watched items and spoilers according to the profile. Confirm streaming availability in the chosen country or say it could not be confirmed; do not infer availability from a different country.
- **Learning/language:** Adapt to subject and level. Cite primary sources, verify technical versions, and provide a usable explanation or exercise. Put challenge answers in a separate private file if they would spoil the exercise.
- **Custom:** Apply the same freshness, provenance, source policy, and exclusion rules; do not invent unsupported data adapters.

## Provenance example

```json
{
  "title": "A verified article title",
  "paragraphs": ["An original summary with context and verified details."],
  "url": "https://example.org/article",
  "source": {
    "publisher": "Example Publisher",
    "url": "https://example.org/article",
    "published_at": "2000-01-01",
    "checked_at": "2000-01-01T07:00:00Z"
  }
}
```

This is a shape example, not a current source. `published_at` can be null when unknown; explain a missing material reference date in the copy. `checked_at` must include a timezone and cannot be later than the issue date in the reader's timezone. All real non-calendar items need source provenance. A source's canonical URL must match its clickable title destination. For an allowlist, both the URL and publisher identity must satisfy the reader's intent; a matching domain alone does not make a claim true.

## Page budget and validation

The renderer respects selected page count and body size and fails on over/underflow. Begin with a feasible article budget. A one-page issue usually needs fewer or shorter sections than a four-page issue. Adjust actual verified copy rather than repeating sentences. Markdown has no fixed pagination.

Render PDFs with Poppler (`pdftoppm -png ...`) or another suitable installed tool and inspect every page. Check masthead, column flow, continuation, title/link destinations, source dates, margins, accents, and readable type. QR codes are vector artwork with a quiet zone, a minimum 64 pt square, and modules at least 0.4 mm wide. Oversized destinations fail rather than producing an unreadably dense code. Inspect and decode a sample with an available QR reader when testing changes. Digital title links remain independently optional.

Generation is manual unless a separate schedule was requested and configured through the host's supported scheduler. Store a validated output before scheduling or printing. Do not claim that a host integration was end-to-end tested when only JSON normalization and rendering were tested.
