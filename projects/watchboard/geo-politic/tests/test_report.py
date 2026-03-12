import unittest
from datetime import datetime, timezone

from geopolitics_watchboard.models import NewsItem
from geopolitics_watchboard.report import classify_bucket, render_report, render_timeline, render_telegram_summary


class ReportTests(unittest.TestCase):
    def test_classify_bucket_uses_keyword_heuristics(self) -> None:
        self.assertEqual(classify_bucket("Navy drill sparks warning"), "escalation")
        self.assertEqual(classify_bucket("Officials resume nuclear talks"), "de-escalation")
        self.assertEqual(classify_bucket("Analysts discuss tanker rates"), "noise")

    def test_timeline_is_chronological(self) -> None:
        items = [
            NewsItem("late", "src", "2026-03-12T10:00:00+00:00", "https://a", "q", "B"),
            NewsItem("early", "src", "2026-03-12T09:00:00+00:00", "https://b", "q", "B"),
        ]
        lines = render_timeline(items)
        self.assertIn("early", lines[0])
        self.assertIn("late", lines[1])

    def test_render_telegram_summary_contains_claim_check_and_tiers(self) -> None:
        items = [
            NewsItem(
                title="Oil could spike to $200 on closure fears",
                source="Reuters",
                published_at="2026-03-12T10:00:00+00:00",
                link="https://www.reuters.com/world/middle-east/sample-story",
                query_tag="oil",
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
        summary_lines = render_telegram_summary("iran-hormuz", items)
        summary = "\n".join(summary_lines)
        self.assertIn("Top claim-check", summary)
        self.assertIn("tier B", summary)
        self.assertIn("tier A", summary)

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
        report = render_report("iran-hormuz", items, ["- custom line"], datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc))
        self.assertIn("## Telegram Brief", report)
        self.assertIn("## Timeline (Chronological)", report)
        self.assertIn("## Claim Check", report)
        self.assertIn("- custom line", report)


if __name__ == "__main__":
    unittest.main()
