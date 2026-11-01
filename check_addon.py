#!/usr/bin/env python3
"""Standalone checks for a My Audiobooks addon repository (standard library only).

Run from the repository root:  python3 -I check_addon.py [--root DIR] [--write-sha] [--strict]

This mirrors the main structural rules of the app's installer (catalog entries, checksums,
capabilities, domains, search URL, mapped field names, URL hosts). It is a subset: the app's
SourcePackage.parse / HtmlSourcePackage.parse is authoritative, so always also Preview the
package in the app. It never makes network requests.

  --write-sha  rewrite each catalog sha256 to match its package file (do this after every edit)
  --strict     treat template placeholders (example domains, 'replace-me' ids) as errors
"""
import argparse, hashlib, json, re, sys
from pathlib import Path
from urllib.parse import urlsplit

ID = re.compile(r'^[a-z0-9][a-z0-9._-]{2,63}$')
VERSION = re.compile(r'^[0-9A-Za-z][0-9A-Za-z.+-]{0,31}$')
HOST = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$')
BLOCKED = ('.local', '.localhost', '.internal', '.lan', '.home', '.onion', '.arpa')
FIELDS = {'id', 'title', 'author', 'description', 'cover', 'series', 'audioUrl', 'tags',
          'durationMs', 'durationSeconds', 'sizeBytes', 'releaseDate', 'narrator',
          'goodreadsRating', 'goodreadsRatingCount', 'goodreadsUrl'}
CAPS = ('catalog.search', 'catalog.details', 'acquisition.resolve', 'library.public')
PLACEHOLDER_HOSTS = ('example.org', 'example.com', 'example.net')

errors, warnings = [], []
def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)

def host_problem(h):
    if h != h.lower() or len(h) > 253 or not HOST.match(h) or re.search(r'\.[0-9]+$', h) or h.endswith(BLOCKED):
        return f"domain '{h}' must be a lowercase public DNS name (no scheme, port, path, wildcard or IP)"

def https_host(url, what, domains=None):
    u = urlsplit(url)
    if u.scheme != 'https' or u.username or u.password or u.port not in (None, 443) or u.fragment or not u.hostname:
        err(f'{what}: must be https with no credentials, port or fragment: {url}'); return None
    if domains is not None and u.hostname not in domains:
        err(f"{what}: host '{u.hostname}' is not in domains")
    return u.hostname

def select(node, path):
    """Tiny subset of the app's JsonPath: a.b, a[].b, a[0].b."""
    nodes = [node]
    for part in filter(None, path.split('.')):
        m = re.fullmatch(r'([A-Za-z0-9_$-]+)(\[(\d*)\])?', part)
        if not m: return []
        nxt = []
        for n in nodes:
            v = n.get(m.group(1)) if isinstance(n, dict) else None
            if v is None: continue
            if m.group(2) is None: nxt.append(v)
            elif m.group(3) == '': nxt.extend(v if isinstance(v, list) else [])
            elif isinstance(v, list) and int(m.group(3)) < len(v): nxt.append(v[int(m.group(3))])
        nodes = nxt
    return nodes

def strings(node):
    if isinstance(node, str): yield node
    elif isinstance(node, dict):
        for v in node.values(): yield from strings(v)
    elif isinstance(node, list):
        for v in node: yield from strings(v)

def check_package(pkg, name):
    domains = pkg.get('domains')
    if not isinstance(domains, list) or not 1 <= len(domains) <= 8 or len(set(domains)) != len(domains):
        err(f'{name}: domains must be 1..8 unique hosts'); domains = []
    for d in domains:
        if (p := host_problem(d)): err(f'{name}: {p}')
        if d.endswith(PLACEHOLDER_HOSTS): warn(f'{name}: placeholder domain {d}')
    if any('REPLACE ME' in s or 'TEMPLATE PLACEHOLDER' in s for s in strings(pkg)): warn(f'{name}: placeholder text remains')
    if 'replace-me' in pkg.get('id', ''): warn(f'{name}: placeholder id {pkg["id"]}')
    if not ID.match(pkg.get('id', '')): err(f'{name}: id must match {ID.pattern}')
    if not VERSION.match(str(pkg.get('version', ''))): err(f'{name}: version is malformed')
    if not str(pkg.get('name', '')).strip(): err(f'{name}: name is required')
    if len(pkg.get('description', '')) > 300: warn(f'{name}: description over 300 characters is truncated')
    if pkg.get('protocolVersion') != 1: err(f'{name}: protocolVersion must be 1')
    execution = pkg.get('execution')
    if execution not in ('declarative-json', 'declarative-html'): err(f'{name}: execution must be declarative-json or declarative-html'); return
    base = pkg.get('baseUrl', '')
    base_host = https_host(base, f'{name}: baseUrl', domains)
    for s in strings(pkg):
        if s.startswith('https://') and s != base:
            https_host(re.sub(r'\{[^}]*\}', 'x', s), f'{name}: URL', domains)
        elif s.startswith(('http://', 'ftp://', 'file://', 'javascript:')):
            err(f'{name}: non-https URL: {s}')
    if execution == 'declarative-html':
        warn(f'{name}: declarative-html is only structure-checked here; Preview it in the app (HtmlSourcePackage.parse is authoritative)')
        return
    caps = pkg.get('capabilities')
    if not isinstance(caps, list) or 'catalog.search' not in caps: err(f'{name}: capabilities must include catalog.search'); caps = []
    for c in caps:
        if c not in CAPS: err(f"{name}: unsupported capability '{c}'")
    if len(set(caps)) != len(caps): err(f'{name}: capabilities contains duplicates')
    if (pkg.get('authentication') or {}).get('type', 'none') != 'none': err(f'{name}: authentication must be none for declarative-json')
    for cap, block in (('catalog.details', 'details'), ('acquisition.resolve', 'acquisition'), ('library.public', 'publicLibrary')):
        if (cap in caps) != (block in pkg): err(f'{name}: capability {cap} and the {block} block must appear together')
    public = pkg.get('publicLibrary')
    if isinstance(public, dict):
        if public.get('format') != 'rss': err(f'{name}: publicLibrary.format must be rss')
        public_url = public.get('url', '')
        if not all(public_url.count('{' + v + '}') == 1 for v in ('profileId', 'shelf', 'page')):
            err(f'{name}: publicLibrary.url needs profileId, shelf and page variables')
        if not isinstance(public.get('shelves'), list) or not public['shelves']:
            err(f'{name}: publicLibrary.shelves must list allowed shelves')
        public_fields = public.get('fields') or {}
        if not all(k in public_fields for k in ('id', 'title', 'author')):
            err(f'{name}: publicLibrary.fields needs id, title and author')
        allowed_public_fields = {'id', 'title', 'author', 'cover', 'description', 'shelves', 'userRating', 'avgRating'}
        for k in public_fields:
            if k not in allowed_public_fields: err(f"{name}: unknown publicLibrary field '{k}'")
    search = pkg.get('search') or {}
    url = search.get('url', '')
    before, _, query = url.partition('?')
    if '{query}' in before or '{query}' not in query: err(f'{name}: search.url needs {{query}} only after "?"')
    if https_host(url.replace('{query}', 'x'), f'{name}: search.url', domains) != base_host: err(f'{name}: search.url host must equal baseUrl host')
    fields = search.get('fields') or {}
    for k in fields:
        if k not in FIELDS: err(f"{name}: unknown field '{k}'")
    for k in ('id', 'title'):
        if k not in fields: err(f'{name}: search.fields must map {k}')
    for block in ('search', 'details'):
        extract = (pkg.get(block) or {}).get('extract') or {}
        for t in extract:
            if t in (pkg[block].get('fields') or {}): err(f"{name}: '{t}' is mapped by both fields and extract")

def check_fixture(pkg, path, name):
    try: data = json.loads(path.read_text())
    except Exception as e: err(f'{name}: fixture {path.name} is not valid JSON ({e})'); return
    search = pkg.get('search') or {}
    items = [i for n in select(data, search.get('resultsPath', '')) for i in (n if isinstance(n, list) else [n])]
    if not items: err(f"{name}: fixture has nothing at resultsPath '{search.get('resultsPath')}'"); return
    for key in ('id', 'title'):
        paths = (search.get('fields') or {}).get(key)
        candidates = [paths] if isinstance(paths, str) else paths or []
        missing = [i for i in items if not any(select(i, p) for p in candidates)]
        if len(missing) == len(items): err(f"{name}: fixture never yields {key} from its fallback paths")
        elif missing: warn(f"{name}: {len(missing)} fixture record(s) lack {key} (they would be skipped)")
    print(f'  {name}: fixture {path.name} -> {len(items)} record(s) reach resultsPath')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', default='.'); ap.add_argument('--write-sha', action='store_true'); ap.add_argument('--strict', action='store_true')
    a = ap.parse_args(); root = Path(a.root).resolve()
    catalog_path = root / 'marketplace.json'
    catalog = json.loads(catalog_path.read_text())
    if catalog.get('catalogVersion') != 1: err('catalogVersion must be 1')
    entries = catalog.get('plugins') or []
    if len(entries) > 200 or len(catalog_path.read_bytes()) > 256 * 1024: err('catalog too large')
    if len({e.get('id') for e in entries}) != len(entries): err('duplicate plugin ids in catalog')
    listed = set()
    for e in entries:
        name = e.get('id', '?')
        if not ID.match(name): err(f'{name}: invalid catalog id')
        if not str(e.get('name', '')).strip() or not VERSION.match(str(e.get('version', ''))): err(f'{name}: catalog name/version missing or malformed')
        if len(e.get('name', '')) > 60 or len(e.get('kind', '')) > 60 or len(e.get('description', '')) > 500: warn(f'{name}: catalog text over limit is truncated')
        if len(e.get('tags', [])) > 12 or any(len(t) > 40 for t in e.get('tags', [])): warn(f'{name}: only 12 tags of 40 characters are kept')
        p = (root / e.get('package', '')).resolve()
        if p.parent != root / 'plugins' or not p.is_file(): err(f'{name}: package must be an existing file directly in plugins/'); continue
        listed.add(p)
        data = p.read_bytes()
        if len(data) > 65536: err(f'{name}: package larger than 64 KB')
        digest = hashlib.sha256(data).hexdigest()
        if digest != e.get('sha256'):
            if a.write_sha:
                e['sha256'] = digest; print(f'  {name}: sha256 updated')
            else: err(f'{name}: sha256 mismatch (expected {digest}); run with --write-sha')
        try: pkg = json.loads(data)
        except Exception: err(f'{name}: package is not valid JSON'); continue
        if pkg.get('id') != e.get('id') or pkg.get('version') != e.get('version'): err(f'{name}: package id/version must equal its catalog entry')
        check_package(pkg, name)
        fx = root / 'fixtures' / (p.name.removesuffix('.source.json') + '.search.json')
        if fx.is_file(): check_fixture(pkg, fx, name)
        else: warn(f'{name}: no fixtures/{fx.name}; save a real sample response there')
    if listed != set((root / 'plugins').glob('*.source.json')): err('every plugins/*.source.json must be listed in marketplace.json')
    if a.write_sha and not errors: catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + '\n')
    if a.strict: errors.extend(f'(strict) {w}' for w in warnings if 'placeholder' in w)
    for w in warnings: print('warning:', w)
    for e in errors: print('error:', e)
    print(f'{len(entries)} entry(ies), {len(errors)} error(s), {len(warnings)} warning(s)')
    sys.exit(1 if errors else 0)

main()
