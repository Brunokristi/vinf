# Biblical Search Engine — crawler checkpoint 2a

Focused, file-based crawler for selected BibleHub document categories.

## Scope

The crawler currently accepts only:

- Bible chapter pages, e.g. `https://biblehub.com/genesis/1.htm`
- aggregated commentary pages, e.g. `https://biblehub.com/commentaries/genesis/1-1.htm`
- topical pages under `/topical/`
- atlas pages under `/atlas/`

It deliberately rejects unrelated BibleHub sections and external domains.

## Architecture

```text
seed_urls.txt
      |
      v
 URL Frontier
      |
      v
URL normalization
      |
      v
allowlist + deduplication
      |
      v
 robots.txt
      |
      v
 rate limiter
      |
      v
HTTP downloader
      |
      +------------------+
      |                  |
      v                  v
 raw HTML          pages.jsonl
      |
      v
link extraction
      |
      v
new eligible URLs
      |
      +----> frontier
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Before a real crawl, replace the placeholder contact address in `crawler/config.py`, or set a complete User-Agent:

```bash
export BSE_USER_AGENT='BiblicalSearchEngine/0.1 (student research project; contact: your-email@example.com)'
```

## Test crawl

Start conservatively:

```bash
python -m crawler --max-pages 5
```

Then run a larger checkpoint sample:

```bash
python -m crawler --max-pages 20
```

The crawler continues from its previous state. It does not remove previous raw pages.

## Output

```text
data/
├── raw/html/                # original HTML responses
├── metadata/pages.jsonl     # crawl metadata
├── metadata/robots.txt      # robots.txt fetched at crawl start
├── metadata/run_summary.json
├── state/seen_urls.txt      # all discovered URLs
├── state/visited_urls.txt   # processed URLs
└── errors/errors.jsonl      # request / robots errors
```

## Statistics

```bash
python scripts/stats.py
```

## Tests

```bash
pytest -q
```

The tests are offline and do not send requests to BibleHub.

## HTTP defaults

- User-Agent: custom project identifier with contact
- Accept: `text/html,application/xhtml+xml`
- Accept-Language: `en-US,en;q=0.9`
- download delay: 3 seconds
- connect timeout: 10 seconds
- read timeout: 20 seconds
- retries: 2
- requests are sequential
- HTTP 429 and 503 use `Retry-After` when available, otherwise exponential backoff
- robots.txt is enforced; if robots.txt cannot be checked, the default policy is to stop crawling

## Five checkpoint samples

After the test crawl:

```bash
python scripts/show_samples.py --limit 5
```

This prints URL, document type, title, HTTP status, response size and raw HTML path for five saved pages.
