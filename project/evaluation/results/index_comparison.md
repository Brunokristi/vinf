# Custom index vs. PyLucene

Scores are not compared directly because the custom backend uses TF-IDF/cosine while Lucene uses its own ranking model.

| Query | Mode | Custom ms | Lucene ms | Top-k overlap |
|---|---:|---:|---:|---:|
| moses egypt | OR | 63.96 | 6.53 | 3/10 (30.0%) |
| moses egypt | AND | 21.01 | 3.00 | 3/10 (30.0%) |
| jesus resurrection | OR | 145.03 | 2.70 | 1/10 (10.0%) |
| jesus resurrection | AND | 26.93 | 1.93 | 1/10 (10.0%) |
| holy spirit | OR | 126.56 | 1.98 | 2/10 (20.0%) |
| holy spirit | AND | 67.18 | 1.94 | 2/10 (20.0%) |
| jerusalem temple | OR | 60.25 | 3.43 | 0/10 (0.0%) |
| jerusalem temple | AND | 20.60 | 1.68 | 0/10 (0.0%) |
| aaron priest | OR | 18.80 | 1.67 | 3/10 (30.0%) |
| aaron priest | AND | 5.27 | 1.59 | 3/10 (30.0%) |
| david king | OR | 88.67 | 1.76 | 2/10 (20.0%) |
| david king | AND | 33.67 | 1.40 | 2/10 (20.0%) |
| paul faith | OR | 195.49 | 1.56 | 3/10 (30.0%) |
| paul faith | AND | 78.25 | 1.68 | 3/10 (30.0%) |
| abraham covenant | OR | 70.65 | 1.18 | 2/10 (20.0%) |
| abraham covenant | AND | 17.12 | 1.04 | 2/10 (20.0%) |

## Summary

- Average custom query time: 64.97 ms
- Average Lucene query time: 2.19 ms
- Average top-k overlap: 20.0%

## Top results

### moses egypt (OR)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Moses Leaves for Egypt |
| 2 |  | Moses with his Wife and Sons, he Leaves Jethro to Perform his Mission in Egypt |
| 3 |  | Evil for Good: Israelites, to Moses |
| 4 |  | Moses Returns to Egypt |
| 5 |  | Uncharitableness: Charging Him With Bringing Them out of Egypt to Die |
| 6 |  | Israel's Rebellion in Egypt |
| 7 |  | Moses: Commissioned As Leader of the Israelites |
| 8 |  | Egypt: Israel in Moses Exposed on the Nile |
| 9 |  | Fugitives: Moses |
| 10 |  | Moses: Learned in all the Wisdom of Egypt |

### moses egypt (AND)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Moses Leaves for Egypt |
| 2 |  | Moses with his Wife and Sons, he Leaves Jethro to Perform his Mission in Egypt |
| 3 |  | Evil for Good: Israelites, to Moses |
| 4 |  | Moses Returns to Egypt |
| 5 |  | Uncharitableness: Charging Him With Bringing Them out of Egypt to Die |
| 6 |  | Israel's Rebellion in Egypt |
| 7 |  | Moses: Commissioned As Leader of the Israelites |
| 8 |  | Egypt: Israel in Moses Exposed on the Nile |
| 9 |  | Fugitives: Moses |
| 10 |  | Moses: Learned in all the Wisdom of Egypt |

### jesus resurrection (OR)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Resurrection Debate |
| 2 |  | The Resurrection: Assumed and Proved by Our Lord |
| 3 |  | The Resurrection: Denied by the Sadducees |
| 4 |  | Jesus Christ, the Risen Lord |
| 5 |  | The Role of the Resurrection |
| 6 |  | Proclaim the Resurrection |
| 7 |  | The Resurrection: Explained Away by False Teachers |
| 8 |  | The Importance of the Resurrection |
| 9 |  | Resurrection as Validation |
| 10 |  | The Resurrection: Saints In, Shall: Rise Through Christ |

### jesus resurrection (AND)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Resurrection Debate |
| 2 |  | The Resurrection: Assumed and Proved by Our Lord |
| 3 |  | The Resurrection: Denied by the Sadducees |
| 4 |  | Jesus Christ, the Risen Lord |
| 5 |  | The Role of the Resurrection |
| 6 |  | Proclaim the Resurrection |
| 7 |  | The Resurrection: Explained Away by False Teachers |
| 8 |  | The Importance of the Resurrection |
| 9 |  | Resurrection as Validation |
| 10 |  | The Resurrection: Saints In, Shall: Rise Through Christ |

### holy spirit (OR)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | The Importance of the Holy Spirit |
| 2 |  | Titles and Names of the Holy Spirit: Holy Spirit |
| 3 |  | Offenses Against the Holy Spirit: Exhibited in Doing Despite to Him |
| 4 |  | Respect for the Holy Spirit |
| 5 |  | The Holiness of the Holy Spirit |
| 6 |  | Seek the Holy Spirit's Empowerment |
| 7 |  | The Holy Spirit: is God: As Jehovah of Hosts |
| 8 |  | the Personality of Holy Spirit: He Can be Grieved |
| 9 |  | The Empowering Presence of the Holy Spirit |
| 10 |  | Offenses Against the Holy Spirit: Exhibited in Danger of Trifling With the Holy Spirit |

### holy spirit (AND)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | The Importance of the Holy Spirit |
| 2 |  | Titles and Names of the Holy Spirit: Holy Spirit |
| 3 |  | Offenses Against the Holy Spirit: Exhibited in Doing Despite to Him |
| 4 |  | Respect for the Holy Spirit |
| 5 |  | The Holiness of the Holy Spirit |
| 6 |  | Seek the Holy Spirit's Empowerment |
| 7 |  | The Holy Spirit: is God: As Jehovah of Hosts |
| 8 |  | the Personality of Holy Spirit: He Can be Grieved |
| 9 |  | The Empowering Presence of the Holy Spirit |
| 10 |  | Offenses Against the Holy Spirit: Exhibited in Danger of Trifling With the Holy Spirit |

### jerusalem temple (OR)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Jesus, the Christ: Revelations by: The Destruction of the Temple, and Jerusalem |
| 2 |  | Jerusalem: Street of the House of God |
| 3 |  | The Jews in Jerusalem |
| 4 |  | Jerusalem: The Temple Built In |
| 5 |  | Jesus, the Christ: Foretells the Destruction of the Temple, and of Jerusalem (In Jerusalem) |
| 6 |  | The Fate of the Temple Vessels |
| 7 |  | Destruction of the Temple |
| 8 |  | Temple: Solomon's: Restoration of, Ordered by Cyrus |
| 9 |  | The Fate of the Temple Articles |
| 10 |  | Adorning and Beautifying Jerusalem |

### jerusalem temple (AND)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Jesus, the Christ: Revelations by: The Destruction of the Temple, and Jerusalem |
| 2 |  | Jerusalem: Street of the House of God |
| 3 |  | The Jews in Jerusalem |
| 4 |  | Jerusalem: The Temple Built In |
| 5 |  | Jesus, the Christ: Foretells the Destruction of the Temple, and of Jerusalem (In Jerusalem) |
| 6 |  | The Fate of the Temple Vessels |
| 7 |  | Destruction of the Temple |
| 8 |  | Temple: Solomon's: Restoration of, Ordered by Cyrus |
| 9 |  | The Fate of the Temple Articles |
| 10 |  | Adorning and Beautifying Jerusalem |

### aaron priest (OR)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Aaron: Descendants of |
| 2 |  | Elea'zar |
| 3 |  | Priestly Lineage |
| 4 |  | The Priestly Line of Aaron |
| 5 |  | the High Priest Christ: Typified: Aaron |
| 6 |  | The High Priest: Specially Called of God |
| 7 |  | The High Priest: The office of, Hereditary |
| 8 |  | Sin Offering for Aaron |
| 9 |  | Ithamar: Son of Aaron |
| 10 |  | Descendants of Aaron |

### aaron priest (AND)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Aaron: Descendants of |
| 2 |  | Elea'zar |
| 3 |  | Priestly Lineage |
| 4 |  | The Priestly Line of Aaron |
| 5 |  | the High Priest Christ: Typified: Aaron |
| 6 |  | The High Priest: Specially Called of God |
| 7 |  | The High Priest: The office of, Hereditary |
| 8 |  | Sin Offering for Aaron |
| 9 |  | Ithamar: Son of Aaron |
| 10 |  | Descendants of Aaron |

### david king (OR)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Toi: King of Hamath |
| 2 |  | Toi |
| 3 |  | Anointing in Consecration: David |
| 4 |  | Tou |
| 5 |  | The Gathering at Hebron |
| 6 |  | Titles and Names of Christ: David |
| 7 |  | Hadade'zer |
| 8 |  | 2 Samuel 5 |
| 9 |  | Servant: Good of Ziba |
| 10 |  | 2 Samuel 8 |

### david king (AND)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Toi: King of Hamath |
| 2 |  | Toi |
| 3 |  | Anointing in Consecration: David |
| 4 |  | Tou |
| 5 |  | The Gathering at Hebron |
| 6 |  | Titles and Names of Christ: David |
| 7 |  | Hadade'zer |
| 8 |  | 2 Samuel 5 |
| 9 |  | Servant: Good of Ziba |
| 10 |  | 2 Samuel 8 |

### paul faith (OR)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Faith: Paul |
| 2 |  | Faith: Faith in Christ: The Corinthians |
| 3 |  | Timothy's Encouraging Report |
| 4 |  | Faith Over Law |
| 5 |  | Justification by Works and Faith |
| 6 |  | Faith: Thessalonians |
| 7 |  | Pursuing Righteousness by Faith |
| 8 |  | Children: Timothy |
| 9 |  | Justification Before God by Faith: Does not Make Void the Law |
| 10 |  | Faith-righteousness |

### paul faith (AND)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | Faith: Paul |
| 2 |  | Faith: Faith in Christ: The Corinthians |
| 3 |  | Timothy's Encouraging Report |
| 4 |  | Faith Over Law |
| 5 |  | Justification by Works and Faith |
| 6 |  | Faith: Thessalonians |
| 7 |  | Pursuing Righteousness by Faith |
| 8 |  | Children: Timothy |
| 9 |  | Justification Before God by Faith: Does not Make Void the Law |
| 10 |  | Faith-righteousness |

### abraham covenant (OR)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | The Covenant with Abraham is Remembered |
| 2 |  | Condescension of God: Enters Into Covenant With Abraham |
| 3 |  | Predestination in the Covenant With Abraham to Have Posterity |
| 4 |  | The Covenant: Made With: Abraham |
| 5 |  | God's Covenant with Abraham |
| 6 |  | Covenant: Abraham and Abimelech |
| 7 |  | Abraham: Circumcision of |
| 8 |  | Oath used in Solemnizing Covenants: Between Abraham and Abimelech |
| 9 |  | The Jews: Descended from Abraham |
| 10 |  | Covenant with the Fathers |

### abraham covenant (AND)

| Rank | Custom | Lucene |
|---:|---|---|
| 1 |  | The Covenant with Abraham is Remembered |
| 2 |  | Condescension of God: Enters Into Covenant With Abraham |
| 3 |  | Predestination in the Covenant With Abraham to Have Posterity |
| 4 |  | The Covenant: Made With: Abraham |
| 5 |  | God's Covenant with Abraham |
| 6 |  | Covenant: Abraham and Abimelech |
| 7 |  | Abraham: Circumcision of |
| 8 |  | Oath used in Solemnizing Covenants: Between Abraham and Abimelech |
| 9 |  | The Jews: Descended from Abraham |
| 10 |  | Covenant with the Fathers |
