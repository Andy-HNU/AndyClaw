import unittest
from datetime import datetime, timezone

from geopolitics_watchboard.models import NewsItem
from geopolitics_watchboard.report import classify_bucket, render_report


class ReportTests(unittest.TestCase):
    def test_classify_bucket_uses_keyword_heuristics(self) -> None:
        self.assertEqual(classify_bucket("Navy drill sparks warning"), "escalation")
        self.assertEqual(classify_bucket("Officials resume nuclear talks"), "de-escalation")
        self.assertEqual(classify_bucket("Analysts discuss tanker rates"), "noise")

    def test_render_report_contains_required_sections(self) -> None:
        items = [
            NewsItem(
                title="Iran warning raises shipping risk",
                source="Reuters",
                published_at="2026-03-12T10:00:00+00:00",
                link="https://www.reuters.com/world/middle-east/sample-story",
                query_tag="shipping",
                tier="B",
            ),
            NewsItem(
                title="Officials resume talks on maritime safety",
                source="state.gov",
                published_at="2026-03-12T09:00:00+00:00",
                link="https://www.state.gov/briefing",
                query_tag="diplomacy",
                tier="A",
            ),
        ]
        report = render_report("iran-hormuz", items, datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc))
        self.assertIn("# Watchboard Report: iran-hormuz", report)
        self.assertIn("## Headline Summary", report)
        self.assertIn("## Buckets", report)
        self.assertIn("## Source-Cited News", report)
        self.assertIn("## Claim Check", report)
        self.assertIn("## Portfolio Impact Template", report)
        self.assertIn("https://www.reuters.com/world/middle-east/sample-story", report)


if __name__ == "__main__":
    unittest.main()
