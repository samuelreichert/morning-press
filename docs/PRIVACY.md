# Privacy and publication boundary

The repository contains skill instructions, schemas, rendering code, documentation, tests, and invented examples. A fresh install has no knowledge of another reader. No migration or search of neighboring folders is performed.

A new reader starts with empty preference fields and no enabled sections. Setup never copies the demo profile. Do not reuse an author's personal information or selections as examples, defaults, source rules, or inferred interests. Only answers explicitly supplied by the current reader may populate their profile. Previously saved profiles are read only when that profile is deliberately selected; they are not templates for new readers.

Profiles and generated editions are private local files outside the package. They may include interests, locations, source preferences, agenda summaries, and browsing-derived editorial content. Private storage is not encrypted by this project. Use an appropriate local account and storage location, and understand any backup/sync service you choose.

This package has no telemetry and its Python helpers make no network requests. When a host agent researches or uses a connector, that host/provider's own processing and permissions still apply. Local rendering does not make an online agent's conversation offline.

Authentication stays with the host's connector or operating system. Do not put passwords, tokens, private subscription URLs, meeting URLs, or account identifiers into JSON profiles. Choose calendar names and scope instead. Calendar copy must follow the reader's details/busy-only choice; its items have no printable URLs.

Public article URLs are restricted to clean HTTPS destinations without query strings or fragments. This reduces accidental exposure through printable QR codes and clickable titles; it is not a full classification of every possible sensitive path. Review destinations editorially. Do not encode a private or tokenized link just because it passes a parser.

## Before a public commit or release

- Keep reader data outside the repository and retain backup `.gitignore` exclusions.
- Add only intended public files and update `public-files.json` deliberately.
- Run `tools/check_public.py --history`. It inspects the Git index and every reachable historical blob, so deleting a sensitive current file alone does not clear old history.
- Inspect the staged diff and verify all examples remain invented. The guard finds common patterns, not arbitrary personal stories, preferences, or identities.
- Never upload real profiles, calendar exports, collection logs, screenshots, newspapers, or private test artifacts as public bug reports or CI artifacts.

Generated PDFs, image previews, state, exports, and environment files are excluded from the public manifest. A maintainer can deliberately expand the manifest later only after reviewing the content and its rights. The MIT license covers the code and supplied original examples, not third-party news or account data.
