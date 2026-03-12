import unittest

from geopolitics_watchboard.sources import load_topics_registry, topic_config, topic_queries


class TopicConfigTests(unittest.TestCase):
    def test_topics_registry_loads_and_has_queries(self) -> None:
        registry = load_topics_registry()
        cfg = topic_config(registry, "iran-hormuz")
        self.assertIn("queries", cfg)
        self.assertGreaterEqual(len(topic_queries(registry, "iran-hormuz")), 1)

    def test_unknown_topic_raises(self) -> None:
        registry = load_topics_registry()
        with self.assertRaises(ValueError):
            topic_config(registry, "not-a-topic")


if __name__ == "__main__":
    unittest.main()
