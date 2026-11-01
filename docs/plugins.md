# Create a source plugin

A plugin is a small declarative JSON manifest: it names public HTTPS endpoints and maps response fields to book metadata. It does not execute code. You can host and share a supported plugin without access to the app source.

This repository includes an Open Library example at `plugins/openlibrary-metadata.source.json`, its catalog in `marketplace.json`, and a real trimmed response under `fixtures/`. It searches book metadata and opens the source’s work page. It provides no audio and does not claim that an audiobook exists. A live API response was captured on 2026-11-01; in-app install and search have not been verified for this public tree.

## Try the example

Install Python 3, download or clone this repository and run from its root:

```sh
python3 -I check_addon.py --strict
```

After the repository is published, open **Profile → Sources → Browse source marketplace → link button** in the app. Paste `https://github.com/nixolas1/kvekk`, choose **Preview**, inspect the domains and capabilities, then install. Search for a known title and confirm that opening the source leads to the correct Open Library page. The install URL uses the repository’s `main` branch. Nothing is silently installed.

## Make your own

1. Work in your own public repository. Start from the example and checker; retain their license and attribution if you copy them.
2. Inspect the real service first. Use its documented, public, unauthenticated HTTPS API. Save a small real response for a known title in `fixtures/<stem>.search.json`. Remove credentials and personal data; establish permission to use and redistribute any retained data.
3. Create `plugins/<stem>.source.json`. Choose a stable lowercase ID, honest name and description, version, exact allowed domains, base URL and search mapping. Map only fields actually provided by the source.
4. Add the package to `marketplace.json`; match its ID, name and version, use a relative `plugins/<stem>.source.json` path and an honest kind such as `Metadata only`.
5. Run `python3 -I check_addon.py --write-sha --strict`, then `python3 -I check_addon.py --strict`. Commit the manifest, fixture and catalog together.
6. Host them on public HTTPS, preview and install in the app, and test a known title and no-results query. Report exactly which checks you completed.
7. Submit a plugin issue with your repository URL, capability summary, license, source permission and validation evidence. A submission is reviewed; it is not automatically included or endorsed.

## Supported JSON manifest subset

| Field | Rule |
| --- | --- |
| `id` | Stable lowercase `[a-z0-9][a-z0-9._-]{2,63}`; never reused for another source |
| `version` | Nonempty version up to 32 allowed characters; same in package and catalog |
| `protocolVersion` / `execution` | `1` / `declarative-json` |
| `capabilities` | `catalog.search` always; optional `catalog.details`, `acquisition.resolve`, `library.public` each require the matching block |
| `domains` | 1–8 exact public DNS hosts; no wildcards, IPs, credentials or local domains |
| `baseUrl` / other URLs | HTTPS, default port, declared hosts; no credentials or fragments; redirects must obey runtime host rules |
| `authentication` | `{ "type": "none" }` for JSON plugins |
| `search.url` | GET URL on the base host; `{query}` appears only after `?` |
| `search.resultsPath` | Path to result array, such as `docs` |
| `search.fields` | At least `id` and `title`; simple paths such as `author_name[]`, `a.b`, `files[0].name`; up to four fallback paths per field |
| Size | Package ≤64 KB; catalog ≤256 KB, ≤200 entries |

Useful mapped fields include `author`, `description`, `cover`, `series`, `tags`, `durationMs`, `durationSeconds`, `sizeBytes`, `releaseDate` and `narrator`. Keep recording-specific price, size, narrator and encoding attached to their actual recording. Shared title matches do not establish those facts.

The example shows safe per-record URL templates: `vars` reads record values and `templates.cover` interpolates them on a declared HTTPS host. `{id:path}` allows a multi-segment ID at the end of a URL path; ordinary `{id}` is one encoded segment. Missing variables drop the field. Never interpolate a host or scheme.

An `acquisition` block with `type: external`, `externalUrl` and a truthful `label` opens the provider’s page; it does not download audio. File acquisition and details need real source-specific mappings and fixture evidence. Do not invent fields or treat previews as full recordings.

## Boundaries

JSON plugins cannot supply API keys, custom headers, cookies, POST bodies, pagination logic, regular expressions, executable code or DRM workarounds. Account integrations or new runtime capabilities require a scoped app change through the contributor process. The app also supports a separate HTML-manifest runtime with bounded selectors and form login; this example and guide cover JSON only. Ask about compatibility before proposing an HTML plugin rather than applying JSON rules to it.

The checker is a standard-library-only offline subset of the installer. It verifies catalog structure, hashes, principal manifest rules and fixture paths for ID/title. It does not execute acquisition/extract rules, validate HTML selectors, check provider terms or prove current network behavior. In-app Preview uses the actual parser; successful search and playback require their own checks.

## Hosting and updates

Catalog and package must share a public HTTPS host. GitHub repository URLs use branch `main`; static HTTPS hosting also works. Private or token-bearing URLs do not work. Never place credentials in a manifest or URL.

Published bytes are immutable: increment package and catalog versions, regenerate SHA-256, and publish both together. Users reinstall updated plugins from the catalog; plugins never update silently. Checksums detect changed bytes, not publisher authenticity. Community catalogs are not the app’s bundled Official catalog.
