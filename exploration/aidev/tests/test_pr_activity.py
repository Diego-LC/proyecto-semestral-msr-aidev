import unittest


from exploration.aidev.pr_activity import (
    build_pr_activity_records,
    compute_overview_metrics,
    select_parquet_urls,
)


class SelectParquetUrlsTests(unittest.TestCase):
    def test_select_parquet_urls_returns_requested_configs(self):
        manifest = {
            "parquet_files": [
                {"config": "pull_request", "split": "train", "url": "https://example/pull.parquet"},
                {"config": "pr_commits", "split": "train", "url": "https://example/commits.parquet"},
                {"config": "pr_reviews", "split": "train", "url": "https://example/reviews.parquet"},
            ]
        }

        selected = select_parquet_urls(manifest, ["pull_request", "pr_reviews"])

        self.assertEqual(
            selected,
            {
                "pull_request": "https://example/pull.parquet",
                "pr_reviews": "https://example/reviews.parquet",
            },
        )


class BuildPrActivityRecordsTests(unittest.TestCase):
    def test_build_pr_activity_records_aggregates_commits_reviews_and_durations(self):
        pull_requests = [
            {
                "id": 100,
                "agent": "Claude_Code",
                "user": "alice",
                "state": "closed",
                "created_at": "2025-07-01T10:00:00Z",
                "closed_at": "2025-07-01T16:00:00Z",
                "merged_at": "2025-07-01T15:00:00Z",
                "repo_id": 1,
                "repo_url": "https://api.github.com/repos/example/repo",
                "html_url": "https://github.com/example/repo/pull/10",
                "number": 10,
            },
            {
                "id": 200,
                "agent": "Codex",
                "user": "bot-author",
                "state": "open",
                "created_at": "2025-07-02T10:00:00Z",
                "closed_at": None,
                "merged_at": None,
                "repo_id": 2,
                "repo_url": "https://api.github.com/repos/example/repo2",
                "html_url": "https://github.com/example/repo2/pull/22",
                "number": 22,
            },
        ]
        commits = [
            {"pr_id": 100, "author": "alice", "committer": "alice", "sha": "a1", "message": "initial"},
            {"pr_id": 100, "author": "bob", "committer": "bob", "sha": "a2", "message": "fix"},
            {"pr_id": 200, "author": "bot-author", "committer": "bot-author", "sha": "b1", "message": "init"},
        ]
        reviews = [
            {
                "pr_id": 100,
                "user": "carol",
                "user_type": "User",
                "state": "APPROVED",
                "submitted_at": "2025-07-01T14:00:00Z",
            },
            {
                "pr_id": 100,
                "user": "coderabbitai[bot]",
                "user_type": "Bot",
                "state": "COMMENTED",
                "submitted_at": "2025-07-01T13:00:00Z",
            },
            {
                "pr_id": 200,
                "user": "bot-author",
                "user_type": "User",
                "state": "COMMENTED",
                "submitted_at": "2025-07-02T11:00:00Z",
            },
        ]

        records = build_pr_activity_records(pull_requests, commits, reviews)

        self.assertEqual(len(records), 2)

        pr100 = records[0]
        self.assertEqual(pr100["pr_id"], 100)
        self.assertTrue(pr100["merged"])
        self.assertEqual(pr100["commit_count"], 2)
        self.assertEqual(pr100["unique_commit_authors_count"], 2)
        self.assertEqual(pr100["external_commit_author_count"], 1)
        self.assertEqual(pr100["review_count"], 2)
        self.assertEqual(pr100["human_review_count"], 1)
        self.assertEqual(pr100["bot_review_count"], 1)
        self.assertEqual(pr100["approved_review_count"], 1)
        self.assertEqual(pr100["commented_review_count"], 1)
        self.assertEqual(pr100["changes_requested_review_count"], 0)
        self.assertTrue(pr100["has_human_review"])
        self.assertTrue(pr100["has_external_human_review"])
        self.assertAlmostEqual(pr100["time_to_close_hours"], 6.0)
        self.assertAlmostEqual(pr100["time_to_merge_hours"], 5.0)

        pr200 = records[1]
        self.assertEqual(pr200["pr_id"], 200)
        self.assertFalse(pr200["merged"])
        self.assertEqual(pr200["commit_count"], 1)
        self.assertEqual(pr200["review_count"], 1)
        self.assertEqual(pr200["human_review_count"], 1)
        self.assertEqual(pr200["bot_review_count"], 0)
        self.assertFalse(pr200["has_external_human_review"])
        self.assertIsNone(pr200["time_to_close_hours"])
        self.assertIsNone(pr200["time_to_merge_hours"])

    def test_compute_overview_metrics_summarizes_records(self):
        records = [
            {
                "merged": True,
                "commit_count": 2,
                "review_count": 1,
                "human_review_count": 1,
                "bot_review_count": 0,
                "has_human_review": True,
                "has_external_human_review": True,
                "time_to_close_hours": 6.0,
                "time_to_merge_hours": 5.0,
            },
            {
                "merged": False,
                "commit_count": 1,
                "review_count": 3,
                "human_review_count": 0,
                "bot_review_count": 3,
                "has_human_review": False,
                "has_external_human_review": False,
                "time_to_close_hours": None,
                "time_to_merge_hours": None,
            },
        ]

        metrics = compute_overview_metrics(records)

        self.assertEqual(metrics["total_prs"], 2)
        self.assertEqual(metrics["merged_prs"], 1)
        self.assertAlmostEqual(metrics["merge_rate"], 0.5)
        self.assertAlmostEqual(metrics["avg_commits_per_pr"], 1.5)
        self.assertAlmostEqual(metrics["avg_reviews_per_pr"], 2.0)
        self.assertEqual(metrics["prs_with_human_reviews"], 1)
        self.assertEqual(metrics["prs_with_external_human_reviews"], 1)
        self.assertEqual(metrics["prs_with_bot_reviews"], 1)
        self.assertAlmostEqual(metrics["avg_time_to_close_hours"], 6.0)
        self.assertAlmostEqual(metrics["avg_time_to_merge_hours"], 5.0)


if __name__ == "__main__":
    unittest.main()
