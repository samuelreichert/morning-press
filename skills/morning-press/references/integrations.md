# Optional integrations

Morning Press is a skill and local renderer, not an OAuth service or calendar client. It uses the capabilities available in the host agent. No account connection is required for installation, setup, or demo. A preference for a provider does not mean that provider is supported by the current machine.

| Reader choice | How to proceed | If unavailable |
| --- | --- | --- |
| No calendar | Omit the section and make no calendar calls | Nothing to configure |
| Google Calendar | Discover a calendar connector, select authorized account/calendar scope, perform a read | Offer manual agenda or user-provided export |
| Apple Calendar | Discover an actual local Calendar capability if one exists, with requested OS permission/scope | Offer an exported ICS file or manual agenda; do not promise a bundled native connector |
| Outlook | Discover an available Outlook Calendar connector and scoped reads | Offer export or manual agenda |
| Notion | Use a connected dated database selected by the reader; confirm date, end date, timezone, and status fields | Offer exported rows/manual agenda; dated tasks are not automatically a complete calendar |
| ICS | Use an available parser with timezone, recurrence, exclusions, and exception handling on a user-selected local file | Ask for a simple agenda instead; this package does not bundle an ICS parser |
| Manual | Use entries explicitly supplied by the reader | Label completeness as reader-supplied |
| Other provider | Discover an appropriate capability and disclose what can actually be read | Keep the preference pending or switch to manual with the reader |

Record provider, mode, state, and calendar names in the private profile. States are `pending`, `connected` (verified connector), `unavailable`, and `manual`. Do not mark a manual import as a connected account. Keep authentication in the connector or OS credential store; never write tokens, passwords, feed URLs, or meeting URLs into profile fields.

Ask about which calendars may be included and details vs busy-only. Do not enumerate unrelated accounts or fetch unselected event bodies. A full-day query uses the publication timezone and timezone-aware start/end instants. If an export lacks enough recurrence information, explain that the agenda may be incomplete. A failed request is not an empty day.

News, forecasts, financial series, event listings, and recommendations likewise use the host's available web/tools. The renderer itself makes no network calls. Store normalized, verified text and source timestamps in the private editorial JSON. Missing capabilities must be disclosed before calling a real edition complete.
