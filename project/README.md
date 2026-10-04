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

# Extractor

The extractor converts saved raw HTML into clean documents for the later full-text index.
It never modifies the original crawl data.

```text
data/raw/html/*.html
        |
        v
    extractor
        |
        +--> data/processed/documents.jsonl
        +--> data/processed/invalid_documents.jsonl
        +--> data/processed/extraction_summary.json
```

The first version uses one content page as one search document:

- `bible` — one Bible chapter; book, chapter and individual verses are retained
- `commentary` — one aggregated commentary page for a chapter or verse
- `topical` — one topical article such as `/topical/m/moses.htm`
- `atlas` — one place article such as `/atlas/jerusalem.htm`, containing occurrences and encyclopedia material when present

Directory pages are crawlable but are **not** search documents. This includes the
`/topical/` and `/atlas/` roots and alphabetical directories such as
`/topical/a.htm` and `/atlas/b.htm`. They are used only to discover links to real
content pages. The extractor also recognizes and skips these pages in metadata
created by older crawler versions, so an existing crawl does not need to be repeated.

URL metadata and content boundaries are recognized with regular expressions. BeautifulSoup is used only to convert the HTML into a robust sequence of visible text fragments and to remove non-content tags such as scripts, forms and iframes. Extraction does not depend on an exact XPath tree.

## Run the extractor

Start with a small sample:

```bash
python -m extractor --limit 5
```

Inspect the extracted text:

```bash
python scripts/show_extracted.py --limit 5
```

Inspect extraction statistics:

```bash
python scripts/extraction_stats.py
```

If any pages fail validation:

```bash
python scripts/show_invalid.py --limit 20
```

When the sample looks correct, process every saved page:

```bash
python -m extractor
```

Running the extractor again rebuilds only the derived files in `data/processed/`. Raw HTML and crawler metadata remain unchanged.

## Extracted document schema

Every valid document contains common fields such as:

```json
{
    "document_id": "...",
    "url": "https://biblehub.com/genesis/1.htm",
    "document_type": "bible",
    "title": "Genesis 1",
    "text": "1 ...\n2 ...",
    "text_length": 4123,
    "word_count": 790,
    "text_hash": "...",
    "valid": true,
    "validation_errors": []
}
```

Type-specific metadata are added as well:

- Bible: `book`, `chapter`, `verse_count`, `verses`
- Commentary: `book`, `chapter`, `verse`, `reference`
- Topical: `topic`
- Atlas: `place`, `has_occurrences`, `has_encyclopedia`

## Validation

The extractor checks that a document has usable text and the metadata required for its type. Invalid pages are not silently discarded. They are written to `data/processed/invalid_documents.jsonl` together with validation errors so that extraction rules can be improved against real examples.
