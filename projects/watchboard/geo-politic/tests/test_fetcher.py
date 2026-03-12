import unittest

from geopolitics_watchboard.fetcher import assign_tier, dedupe_items, parse_feed
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
        config = {"tiers": {"A": [], "B": ["reuters.com"], "C": []}}
        items = parse_feed(RSS_SAMPLE, "Reuters World", "shipping", config)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.title, "Iran warning raises shipping risk")
        self.assertEqual(item.source, "Reuters")
        self.assertEqual(item.query_tag, "shipping")
        self.assertEqual(item.tier, "B")
        self.assertEqual(item.link, "https://www.reuters.com/world/middle-east/sample-story")

    def test_assign_tier_falls_back_to_c(self) -> None:
        config = {"tiers": {"A": ["state.gov"], "B": ["reuters.com"], "C": ["news.google.com"]}}
        self.assertEqual(assign_tier("https://www.state.gov/briefing", config), "A")
        self.assertEqual(assign_tier("https://www.reuters.com/world", config), "B")
        self.assertEqual(assign_tier("https://example.com/story", config), "C")

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


if __name__ == "__main__":
    unittest.main()
