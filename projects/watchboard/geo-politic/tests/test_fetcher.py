import unittest

from geopolitics_watchboard.fetcher import (
    assign_tier,
    dedupe_items,
    normalize_publisher_name,
    parse_feed,
    preferred_hostname,
)
from geopolitics_watchboard.models import NewsItem


RSS_SAMPLE = """\
<rss version="2.0">
  <channel>
    <title>Sample</title>
    <item>
      <title>Iran warning raises shipping risk</title>
      <link>https://www.reuters.com/world/middle-east/sample-story</link>
      <pubDate>Thu, 12 Mar 2026 10:00:00 GMT</pubDate>
      <source>Reuters</source>
    </item>
  </channel>
</rss>
"""


class FetcherTests(unittest.TestCase):
    def test_parse_feed_normalizes_rss_item(self) -> None:
        config = _source_config()
        items = parse_feed(RSS_SAMPLE, "Reuters World", "shipping", config)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.title, "Iran warning raises shipping risk")
        self.assertEqual(item.source, "Reuters")
        self.assertEqual(item.query_tag, "shipping")
        self.assertEqual(item.tier, "B")
        self.assertEqual(item.link, "https://www.reuters.com/world/middle-east/sample-story")

    def test_assign_tier_falls_back_to_c(self) -> None:
        config = _source_config()
        self.assertEqual(assign_tier("https://www.state.gov/briefing", config), "A")
        self.assertEqual(assign_tier("https://www.reuters.com/world", config), "B")
        self.assertEqual(assign_tier("https://example.com/story", config), "C")

    def test_normalize_publisher_name_strips_punctuation_and_whitespace(self) -> None:
        self.assertEqual(normalize_publisher_name("  The New   York Times. "), "the new york times")
        self.assertEqual(normalize_publisher_name("AP-News"), "ap news")

    def test_preferred_hostname_uses_final_url_parameter(self) -> None:
        link = "https://news.google.com/rss/articles/test?url=https://www.reuters.com/world"
        self.assertEqual(preferred_hostname(link), "reuters.com")

    def test_assign_tier_matches_major_publishers_by_alias_or_final_url(self) -> None:
        config = _source_config()
        cases = [
            ("https://www.reuters.com/world", "Reuters"),
            ("https://news.google.com/rss/articles/xyz?url=https://apnews.com/article/iran", "Associated Press"),
            ("https://www.bloomberg.com/news/articles/2026-03-12/oil", "Bloomberg News"),
            ("https://www.ft.com/content/test-story", "Financial Times"),
            ("https://www.bbc.co.uk/news/world-middle-east-123456", "BBC News"),
            ("https://www.cnbc.com/2026/03/12/oil.html", "CNBC"),
            ("https://www.wsj.com/world/middle-east/story", "The Wall Street Journal"),
            ("https://example.com/redirect?url=https://example.com/not-wsj", "WSJ"),
            ("https://example.com/story", "AP-News"),
            ("https://example.com/story", "  Bloomberg News  "),
        ]
        for link, source in cases:
            with self.subTest(link=link, source=source):
                self.assertEqual(assign_tier(link, config, source=source), "B")

    def test_dedupe_items_removes_near_duplicate_titles_and_tracking_urls(self) -> None:
        items = [
            NewsItem(
                title="Iran warns over Hormuz shipping lane",
                source="Reuters",
                published_at="2026-03-12T11:00:00+00:00",
                link="https://example.com/story?utm_source=x",
                query_tag="shipping",
                tier="B",
            ),
            NewsItem(
                title="Iran warns over Hormuz shipping lanes",
                source="AP",
                published_at="2026-03-12T10:59:00+00:00",
                link="https://example.com/story",
                query_tag="shipping",
                tier="B",
            ),
        ]
        deduped = dedupe_items(items)
        self.assertEqual(len(deduped), 1)


def _source_config() -> dict:
    return {
        "tiers": {
            "A": [
                {"domains": ["state.gov"], "aliases": ["State Department", "U.S. Department of State"]},
            ],
            "B": [
                {"domains": ["reuters.com"], "aliases": ["Reuters"]},
                {"domains": ["apnews.com"], "aliases": ["AP", "AP News", "Associated Press"]},
                {"domains": ["bloomberg.com"], "aliases": ["Bloomberg", "Bloomberg News"]},
                {"domains": ["ft.com"], "aliases": ["FT", "Financial Times"]},
                {"domains": ["bbc.com", "bbc.co.uk"], "aliases": ["BBC", "BBC News"]},
                {"domains": ["cnbc.com"], "aliases": ["CNBC"]},
                {"domains": ["wsj.com"], "aliases": ["WSJ", "Wall Street Journal", "The Wall Street Journal"]},
                {"domains": ["nytimes.com"], "aliases": ["NYT", "NYTimes", "The New York Times"]},
            ],
            "C": [{"domains": ["news.google.com"], "aliases": ["Google News"]}],
        }
    }


if __name__ == "__main__":
    unittest.main()
