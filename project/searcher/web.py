from __future__ import annotations

import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse
import webbrowser

from indexer.idf import SUPPORTED_IDF_METHODS
from .engine import ScoreExplanation, SearchEngine, SearchResponse


PAGE_SIZE = 10

CSS = r"""
:root {
    color-scheme: light;
    --text: #202124;
    --muted: #5f6368;
    --border: #dadce0;
    --link: #1a0dab;
    --url: #137333;
    --surface: #f8f9fa;
    --mark: #fff2a8;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    color: var(--text);
    background: white;
}
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
.header {
    border-bottom: 1px solid var(--border);
    padding: 22px 28px 18px;
}
.brand {
    font-size: 22px;
    font-weight: 700;
    margin-right: 26px;
    white-space: nowrap;
}
.search-row {
    display: flex;
    align-items: center;
    gap: 10px;
    max-width: 1100px;
}
.search-box {
    flex: 1;
    max-width: 690px;
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 12px 18px;
    font-size: 16px;
    outline: none;
    box-shadow: 0 1px 6px rgba(32,33,36,.12);
}
select, button {
    border: 1px solid var(--border);
    background: white;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
}
button { cursor: pointer; background: #1a73e8; color: white; border-color: #1a73e8; }
.container { max-width: 900px; margin-left: 170px; padding: 24px 28px 80px; }
.home { margin: 130px auto 0; max-width: 720px; text-align: center; padding: 24px; }
.home .brand { display: block; font-size: 42px; margin: 0 0 28px; }
.home .search-row { justify-content: center; }
.stats { color: var(--muted); font-size: 14px; margin-bottom: 24px; }
.result { margin-bottom: 30px; max-width: 720px; }
.result-title { font-size: 20px; line-height: 1.3; }
.internal-url { color: var(--url); font-size: 13px; margin: 4px 0 6px; overflow-wrap: anywhere; }
.result-meta { color: var(--muted); font-size: 13px; margin: 5px 0; }
.snippet { font-size: 14px; line-height: 1.58; color: #4d5156; }
mark { background: var(--mark); padding: 0 .08em; border-radius: 2px; }
.breadcrumb { color: var(--muted); font-size: 14px; margin-bottom: 18px; }
.document-title { font-size: 32px; margin: 0 0 8px; }
.badges { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0 24px; }
.badge { background: var(--surface); border: 1px solid var(--border); border-radius: 999px; padding: 5px 10px; font-size: 12px; }
.card { border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin: 18px 0; }
.card h2 { font-size: 20px; margin: 0 0 16px; }
.card h3 { font-size: 16px; margin: 22px 0 10px; }
.meta-grid { display: grid; grid-template-columns: 180px minmax(0, 1fr); gap: 8px 18px; font-size: 14px; }
.meta-grid dt { color: var(--muted); }
.meta-grid dd { margin: 0; overflow-wrap: anywhere; }
.formula { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--surface); border-radius: 8px; padding: 12px 14px; margin: 8px 0; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: right; padding: 8px 7px; border-bottom: 1px solid var(--border); white-space: nowrap; }
th:first-child, td:first-child { text-align: left; }
th { color: var(--muted); font-weight: 600; }
.math-summary { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 14px; }
.math-box { background: var(--surface); border-radius: 10px; padding: 14px; }
.math-box strong { display:block; margin-bottom:8px; }
.document-text { white-space: pre-wrap; line-height: 1.72; font-family: Georgia, 'Times New Roman', serif; font-size: 16px; }
details summary { cursor: pointer; font-weight: 600; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; }
.error { color: #b3261e; background: #fce8e6; padding: 14px; border-radius: 8px; }
@media (max-width: 900px) {
    .container { margin-left: 0; }
    .search-row { flex-wrap: wrap; }
    .search-box { min-width: 100%; }
    .math-summary { grid-template-columns: 1fr; }
    .meta-grid { grid-template-columns: 120px minmax(0,1fr); }
}
"""


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def highlight(value: str, terms: tuple[str, ...]) -> str:
    escaped = html.escape(value)
    unique = sorted({term for term in terms if term}, key=len, reverse=True)
    if not unique:
        return escaped
    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(html.escape(term)) for term in unique) + r")(?!\w)",
        re.IGNORECASE,
    )
    return pattern.sub(r"<mark>\1</mark>", escaped)


def best_snippet(text: str, terms: tuple[str, ...], radius: int = 210) -> str:
    compact = " ".join(text.split())
    if not compact:
        return ""

    term_patterns = [
        re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE)
        for term in terms
        if term
    ]
    candidates: list[tuple[int, int, int]] = []

    for pattern in term_patterns:
        for match in pattern.finditer(compact):
            start = max(0, match.start() - radius)
            end = min(len(compact), match.end() + radius)
            window = compact[start:end]
            unique_hits = sum(bool(p.search(window)) for p in term_patterns)
            all_hits = sum(len(p.findall(window)) for p in term_patterns)
            candidates.append((unique_hits * 100 + all_hits, start, end))

    if candidates:
        _score, start, end = max(candidates, key=lambda item: (item[0], -item[1]))
    else:
        start, end = 0, min(len(compact), radius * 2)

    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(compact) else ""
    return prefix + compact[start:end].strip() + suffix


def layout(body: str, *, title: str, header: str = "") -> bytes:
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
{header}
{body}
</body>
</html>"""
    return page.encode("utf-8")


def search_form(query: str, idf_method: str, mode: str) -> str:
    options_idf = "".join(
        f'<option value="{esc(method)}" {"selected" if method == idf_method else ""}>{esc(method)}</option>'
        for method in SUPPORTED_IDF_METHODS
    )
    options_mode = "".join(
        f'<option value="{candidate}" {"selected" if candidate == mode else ""}>{candidate.upper()}</option>'
        for candidate in ("or", "and")
    )
    return f"""
<form action="/" method="get" class="search-row">
    <input class="search-box" name="q" value="{esc(query)}" placeholder="Search Bible, commentary, topics, atlas..." autofocus>
    <select name="idf" title="IDF method">{options_idf}</select>
    <select name="mode" title="Default Boolean mode">{options_mode}</select>
    <button type="submit">Search</button>
</form>
"""


def header(query: str, idf_method: str, mode: str) -> str:
    return f"""
<header class="header">
    <div class="search-row">
        <a class="brand" href="/">Biblical Search</a>
        {search_form(query, idf_method, mode)}
    </div>
</header>
"""


def render_home(engine: SearchEngine) -> bytes:
    body = f"""
<main class="home">
    <span class="brand">Biblical Search</span>
    {search_form("", "classic", "or")}
    <p class="stats">{engine.document_count:,} locally extracted documents · custom TF-IDF index</p>
</main>
"""
    return layout(body, title="Biblical Search")


def render_results(
    engine: SearchEngine,
    response: SearchResponse,
    raw_query: str,
    host: str,
) -> bytes:
    terms = response.query.terms
    result_blocks: list[str] = []

    for result in response.results:
        doc = result.document
        doc_number = int(doc["doc_number"])
        source = engine.source_document(doc_number)
        snippet = best_snippet(str(source.get("text") or ""), terms)
        params = urlencode({
            "q": raw_query,
            "idf": response.idf_method,
            "mode": response.mode,
            "rank": result.rank,
            "hits": response.total_hits,
        })
        detail_path = f"/document/{doc_number}?{params}"
        internal_url = f"http://{host}{detail_path}"
        meta = [str(doc.get("document_type") or "document")]
        if doc.get("source_collection"):
            meta.append(str(doc["source_collection"]))
        meta.append(f"score {result.score:.6f}")
        meta.append("matched " + ", ".join(result.matched_terms))

        result_blocks.append(f"""
<article class="result">
    <a class="result-title" href="{esc(detail_path)}">{esc(doc.get('title') or 'Untitled document')}</a>
    <div class="internal-url">{esc(internal_url)}</div>
    <div class="result-meta">{esc(' · '.join(meta))}</div>
    <div class="snippet">{highlight(snippet, terms)}</div>
</article>
""")

    body = f"""
<main class="container">
    <div class="stats">
        {response.total_hits:,} matching documents · {response.elapsed_seconds * 1000:.1f} ms ·
        parsed as <strong>{esc(response.query.display)}</strong> · {esc(response.idf_method)} IDF
    </div>
    {''.join(result_blocks) if result_blocks else '<p>No results.</p>'}
</main>
"""
    return layout(
        body,
        title=f"{raw_query} - Biblical Search",
        header=header(raw_query, response.idf_method, response.mode),
    )


def formula_name(method: str) -> str:
    if method == "classic":
        return "IDF(t) = ln(N / df(t))"
    return "IDF(t) = ln((N + 1) / (df(t) + 1)) + 1"


def explanation_table(explanation: ScoreExplanation) -> str:
    rows = []
    for row in explanation.terms:
        if explanation.idf_method == "classic":
            evaluated_idf = (
                f"ln({explanation.document_count:,} / {row.document_frequency:,}) = {row.idf:.6f}"
            )
        else:
            evaluated_idf = (
                f"ln(({explanation.document_count:,} + 1) / "
                f"({row.document_frequency:,} + 1)) + 1 = {row.idf:.6f}"
            )
        rows.append(f"""
<tr>
    <td>{esc(row.term)}</td>
    <td>{row.query_tf}</td>
    <td>{row.document_tf}</td>
    <td>{row.document_frequency:,}</td>
    <td>{row.query_tf_weight:.6f}</td>
    <td>{row.document_tf_weight:.6f}</td>
    <td>{row.idf:.6f}</td>
    <td>{row.query_weight:.6f}</td>
    <td>{row.document_weight:.6f}</td>
    <td>{row.dot_contribution:.6f}</td>
</tr>
<tr>
    <td colspan="10" style="text-align:left;color:#5f6368;padding-top:0">IDF evaluation: {esc(evaluated_idf)}</td>
</tr>
""")

    return f"""
<table>
<thead>
<tr>
    <th>term</th><th>qTF</th><th>dTF</th><th>df</th>
    <th>1+ln(qTF)</th><th>1+ln(dTF)</th><th>IDF</th>
    <th>qWeight</th><th>dWeight</th><th>dot contribution</th>
</tr>
</thead>
<tbody>{''.join(rows)}</tbody>
</table>
"""


def render_math(explanation: ScoreExplanation) -> str:
    denominator = explanation.denominator
    return f"""
<div class="card">
    <h2>Ranking mathematics — {esc(explanation.idf_method)} IDF</h2>
    <div class="formula">TFweight(tf) = 1 + ln(tf), when tf &gt; 0</div>
    <div class="formula">{esc(formula_name(explanation.idf_method))}</div>
    <div class="formula">weight(t,d) = TFweight(t,d) × IDF(t)</div>
    <div class="formula">dot(q,d) = Σ qWeight(t) × dWeight(t)</div>
    <div class="formula">cosine(q,d) = dot(q,d) / (||q|| × ||d||)</div>

    <h3>Per-term calculation</h3>
    {explanation_table(explanation)}

    <h3>Final cosine calculation</h3>
    <div class="math-summary">
        <div class="math-box"><strong>Dot product</strong>{explanation.dot_product:.9f}</div>
        <div class="math-box"><strong>Query norm ||q||</strong>{explanation.query_norm:.9f}</div>
        <div class="math-box"><strong>Document norm ||d||</strong>{explanation.document_norm:.9f}</div>
        <div class="math-box"><strong>Denominator</strong>{denominator:.9f}</div>
    </div>
    <div class="formula">
        score = {explanation.dot_product:.9f} / ({explanation.query_norm:.9f} × {explanation.document_norm:.9f})<br>
        score = {explanation.dot_product:.9f} / {denominator:.9f}<br>
        <strong>score = {explanation.score:.9f}</strong>
    </div>
    <p class="stats">The document norm contains weights of all indexed terms in the document, not only the query terms.</p>
</div>
"""


def render_document(
    engine: SearchEngine,
    doc_number: int,
    *,
    query: str,
    idf_method: str,
    mode: str,
    rank: int | None,
    hits: int | None,
) -> bytes:
    catalog = engine.catalog_document(doc_number)
    source = engine.source_document(doc_number)
    parsed = engine.parse_query(query, default_mode=mode) if query else None
    terms = parsed.terms if parsed else ()

    metadata = dict(source)
    text = str(metadata.pop("text", ""))

    common_fields = [
        ("Local document", f"/document/{doc_number}"),
        ("doc_number", doc_number),
        ("document_id", source.get("document_id")),
        ("title", source.get("title") or catalog.get("title")),
        ("document_type", source.get("document_type")),
        ("source_collection", source.get("source_collection")),
        ("token_count (indexer)", catalog.get("token_count")),
        ("text_length", source.get("text_length")),
        ("word_count", source.get("word_count")),
        ("text_hash", source.get("text_hash")),
    ]
    metadata_html = "".join(
        f"<dt>{esc(name)}</dt><dd>{esc(value)}</dd>"
        for name, value in common_fields
        if value is not None
    )

    original_url = source.get("url") or catalog.get("url")
    if original_url:
        metadata_html += (
            f"<dt>Original source</dt><dd><a href=\"{esc(original_url)}\" target=\"_blank\" "
            f"rel=\"noopener noreferrer\">{esc(original_url)}</a></dd>"
        )

    math_html = ""
    search_context = ""
    if query:
        explanation = engine.explain_document(
            query,
            doc_number,
            idf_method=idf_method,
            mode=mode,
        )
        alternate_method = "smooth" if idf_method == "classic" else "classic"
        alternate = engine.explain_document(
            query,
            doc_number,
            idf_method=alternate_method,
            mode=mode,
        )
        matched = [row.term for row in explanation.terms if row.document_tf > 0]
        rank_text = f"#{rank}" if rank is not None else "—"
        hit_text = f"{hits:,}" if hits is not None else "—"
        search_context = f"""
<div class="card">
    <h2>Why this document was returned</h2>
    <dl class="meta-grid">
        <dt>Query</dt><dd>{esc(explanation.query.display)}</dd>
        <dt>Boolean mode</dt><dd>{esc(mode.upper())}</dd>
        <dt>Matched terms</dt><dd>{esc(', '.join(matched))}</dd>
        <dt>Result rank</dt><dd>{esc(rank_text)}</dd>
        <dt>Matching documents</dt><dd>{esc(hit_text)}</dd>
        <dt>Selected IDF</dt><dd>{esc(idf_method)}</dd>
        <dt>Selected score</dt><dd>{explanation.score:.9f}</dd>
    </dl>
    <h3>Same document under both IDF methods</h3>
    <div class="math-summary">
        <div class="math-box"><strong>{esc(idf_method)}</strong>{explanation.score:.9f}</div>
        <div class="math-box"><strong>{esc(alternate_method)}</strong>{alternate.score:.9f}</div>
    </div>
</div>
"""
        math_html = render_math(explanation) + render_math(alternate)

    raw_metadata = json.dumps(metadata, ensure_ascii=False, indent=4)
    back_params = urlencode({"q": query, "idf": idf_method, "mode": mode}) if query else ""
    back_link = f"/?{back_params}" if back_params else "/"

    body = f"""
<main class="container">
    <div class="breadcrumb"><a href="{esc(back_link)}">← Back to search results</a></div>
    <h1 class="document-title">{esc(source.get('title') or catalog.get('title') or 'Document')}</h1>
    <div class="badges">
        <span class="badge">local extracted document</span>
        <span class="badge">{esc(source.get('document_type') or 'document')}</span>
        {f'<span class="badge">{esc(source.get("source_collection"))}</span>' if source.get('source_collection') else ''}
    </div>

    <div class="card">
        <h2>Document metadata</h2>
        <dl class="meta-grid">{metadata_html}</dl>
        <details style="margin-top:18px">
            <summary>Show complete extracted metadata JSON</summary>
            <pre>{esc(raw_metadata)}</pre>
        </details>
    </div>

    {search_context}
    {math_html}

    <div class="card">
        <h2>Complete extracted document</h2>
        <div class="document-text">{highlight(text, terms)}</div>
    </div>
</main>
"""
    return layout(
        body,
        title=str(source.get("title") or catalog.get("title") or "Document"),
        header=header(query, idf_method, mode),
    )


class SearchRequestHandler(BaseHTTPRequestHandler):
    engine: SearchEngine

    def send_html(self, content: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        path = parsed_url.path

        try:
            if path == "/":
                query = params.get("q", [""])[0].strip()
                idf_method = params.get("idf", ["classic"])[0]
                mode = params.get("mode", ["or"])[0]
                if idf_method not in SUPPORTED_IDF_METHODS:
                    idf_method = "classic"
                if mode not in {"and", "or"}:
                    mode = "or"

                if not query:
                    self.send_html(render_home(self.engine))
                    return

                response = self.engine.search_detailed(
                    query,
                    idf_method=idf_method,
                    mode=mode,
                    limit=PAGE_SIZE,
                )
                self.send_html(
                    render_results(
                        self.engine,
                        response,
                        query,
                        self.headers.get("Host") or "127.0.0.1:8000",
                    )
                )
                return

            match = re.fullmatch(r"/document/(\d+)", path)
            if match:
                doc_number = int(match.group(1))
                if not 0 <= doc_number < self.engine.document_count:
                    self.send_error(404, "Document not found")
                    return

                query = params.get("q", [""])[0].strip()
                idf_method = params.get("idf", ["classic"])[0]
                mode = params.get("mode", ["or"])[0]
                rank_raw = params.get("rank", [""])[0]
                hits_raw = params.get("hits", [""])[0]
                rank = int(rank_raw) if rank_raw.isdigit() else None
                hits = int(hits_raw) if hits_raw.isdigit() else None

                if idf_method not in SUPPORTED_IDF_METHODS:
                    idf_method = "classic"
                if mode not in {"and", "or"}:
                    mode = "or"

                self.send_html(
                    render_document(
                        self.engine,
                        doc_number,
                        query=query,
                        idf_method=idf_method,
                        mode=mode,
                        rank=rank,
                        hits=hits,
                    )
                )
                return

            self.send_error(404, "Not found")
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            body = layout(
                f'<main class="container"><div class="error">{esc(exc)}</div></main>',
                title="Search error",
            )
            self.send_html(body, status=400)

    def log_message(self, format: str, *args) -> None:
        print(f"[web] {self.address_string()} - {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Biblical Search web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    engine = SearchEngine(Path.cwd())

    handler_class = type(
        "ConfiguredSearchRequestHandler",
        (SearchRequestHandler,),
        {"engine": engine},
    )
    server = ThreadingHTTPServer((args.host, args.port), handler_class)
    url = f"http://{args.host}:{args.port}/"

    print("Biblical Search Engine")
    print(f"Documents: {engine.document_count:,}")
    print(f"Vocabulary: {len(engine.lexicon):,}")
    print(f"Open: {url}")
    print("Press Ctrl+C to stop.")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
