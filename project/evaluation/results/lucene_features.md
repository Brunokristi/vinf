# PyLucene feature evaluation

The following tests demonstrate query types that are available in the PyLucene backend.

| Feature | Query | Median time | Results shown |
|---|---|---:|---:|
| Phrase | `holy spirit` | 8.84 ms | 5 |
| Fuzzy | `jeruslem` | 11.68 ms | 5 |
| Boolean AND | `moses egypt` | 7.85 ms | 5 |
| Boolean OR | `moses egypt` | 3.48 ms | 5 |
| Field filter | `moses` | 5.26 ms | 5 |
| Book filter | `jesus` | 2.28 ms | 5 |
| Chapter range | `jesus` | 2.71 ms | 5 |
| Wikipedia reference range | `moses` | 1.28 ms | 5 |
| Combined query | `moses egypt` | 2.13 ms | 5 |

Average query time: **5.06 ms**.

## Individual tests

### Phrase

Exact phrase search over Lucene text fields.

Query: `holy spirit`

Median time: **8.84 ms**

Top results:

1. Holy Spirit: Antediluvians
2. Holy Spirit: Saul
3. Holy Spirit: Israelites
4. Holy Spirit: Samson
5. Holy Spirit: Sin Against

### Fuzzy

Typo-tolerant search using edit distance 1.

Query: `jeruslem`

Median time: **11.68 ms**

Top results:

1. Jerusalem: New Jerusalem
2. Jerusalem:
3. Jerusalem
4. Jerusalem: Beloved
5. Jerusalem: Stairs

### Boolean AND

Both query terms must occur in the document.

Query: `moses egypt`

Median time: **7.85 ms**

Top results:

1. Moses: Learned in all the Wisdom of Egypt
2. Egypt: The Country of: Magi of
3. Egypt: The Country of: Symbolical
4. Egypt: The Country of: Priests of
5. Moses: Under Divine Direction Brings Plagues Upon the Land of Egypt

### Boolean OR

At least one query term may occur in the document.

Query: `moses egypt`

Median time: **3.48 ms**

Top results:

1. Egypt
2. Moses: Learned in all the Wisdom of Egypt
3. Egypt: The Country of: Magi of
4. Egypt: The Country of: Symbolical
5. Egypt: The Country of: Priests of

### Field filter

Full-text search restricted to the commentary crawl group.

Query: `moses`

Median time: **5.26 ms**

Top results:

1. Numbers 3:1 Commentaries
2. Deuteronomy 34:9 Commentaries
3. Deuteronomy 34:12 Commentaries
4. Numbers 12:2 Commentaries
5. Exodus 33:9 Commentaries

### Book filter

Full-text search restricted to the Book of John.

Query: `jesus`

Median time: **2.28 ms**

Top results:

1. John 21
2. John 18
3. John 11
4. John 20
5. John 19

### Chapter range

Full-text search restricted to chapters 1 through 10.

Query: `jesus`

Median time: **2.71 ms**

Top results:

1. John 6
2. John 4
3. John 2
4. John 4:44 Commentaries
5. John 4:47 Commentaries

### Wikipedia reference range

Search only documents enriched from Wikipedia pages with at least 20 references.

Query: `moses`

Median time: **1.28 ms**

Top results:

1. Moses: People Complain Against Moses and Aaron
2. Moses: Prophecies of
3. Moses: His Virility
4. Moses: Face of, Transfigured
5. Moses: Character of Unaspiring

### Combined query

Boolean AND search combined with a crawl-group filter.

Query: `moses egypt`

Median time: **2.13 ms**

Top results:

1. Moses: Learned in all the Wisdom of Egypt
2. Egypt: The Country of: Magi of
3. Egypt: The Country of: Symbolical
4. Egypt: The Country of: Priests of
5. Moses: Under Divine Direction Brings Plagues Upon the Land of Egypt
