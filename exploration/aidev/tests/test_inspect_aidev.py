import unittest


from exploration.aidev.inspect_aidev import pick_default_fields, summarize_rows


class PickDefaultFieldsTests(unittest.TestCase):
    def test_pick_default_fields_prefers_known_aidev_columns(self):
        columns = [
            "id",
            "state",
            "agent",
            "user",
            "created_at",
            "closed_at",
            "merged_at",
            "repo_id",
        ]

        fields = pick_default_fields(columns)

        self.assertEqual(
            fields,
            {
                "tracked_fields": [
                    "state",
                    "agent",
                    "user",
                    "created_at",
                    "closed_at",
                    "merged_at",
                    "repo_id",
                ],
                "categorical_fields": ["state", "agent", "user", "repo_id"],
                "date_fields": ["created_at", "closed_at", "merged_at"],
            },
        )


class SummarizeRowsTests(unittest.TestCase):
    def test_summarize_rows_computes_nulls_counts_and_date_ranges(self):
        rows = [
            {
                "state": "closed",
                "agent": "Claude_Code",
                "user": "alice",
                "created_at": "2025-07-25T18:15:36Z",
                "closed_at": "2025-07-25T19:17:23Z",
                "merged_at": "2025-07-25T19:17:23Z",
                "repo_id": 10,
            },
            {
                "state": "open",
                "agent": None,
                "user": "bob",
                "created_at": "2025-07-26T18:15:36Z",
                "closed_at": None,
                "merged_at": None,
                "repo_id": 10,
            },
            {
                "state": "closed",
                "agent": "Codex",
                "user": "alice",
                "created_at": "2025-07-24T18:15:36Z",
                "closed_at": "2025-07-24T19:17:23Z",
                "merged_at": None,
                "repo_id": 20,
            },
        ]

        summary = summarize_rows(
            rows,
            tracked_fields=[
                "state",
                "agent",
                "user",
                "created_at",
                "closed_at",
                "merged_at",
                "repo_id",
            ],
            categorical_fields=["state", "agent", "user", "repo_id"],
            date_fields=["created_at", "closed_at", "merged_at"],
            top_k=2,
        )

        self.assertEqual(summary["rows_seen"], 3)
        self.assertEqual(summary["null_counts"]["agent"], 1)
        self.assertEqual(summary["null_counts"]["closed_at"], 1)
        self.assertEqual(summary["null_counts"]["merged_at"], 2)
        self.assertEqual(summary["value_counts"]["state"], {"closed": 2, "open": 1})
        self.assertEqual(summary["value_counts"]["agent"], {"Claude_Code": 1, "Codex": 1})
        self.assertEqual(summary["value_counts"]["user"], {"alice": 2, "bob": 1})
        self.assertEqual(summary["value_counts"]["repo_id"], {"10": 2, "20": 1})
        self.assertEqual(
            summary["date_ranges"]["created_at"],
            {"min": "2025-07-24T18:15:36Z", "max": "2025-07-26T18:15:36Z"},
        )
        self.assertEqual(
            summary["date_ranges"]["closed_at"],
            {"min": "2025-07-24T19:17:23Z", "max": "2025-07-25T19:17:23Z"},
        )
        self.assertEqual(
            summary["date_ranges"]["merged_at"],
            {"min": "2025-07-25T19:17:23Z", "max": "2025-07-25T19:17:23Z"},
        )


if __name__ == "__main__":
    unittest.main()
