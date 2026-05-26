import unittest


from exploration.aidev.preparation.rejection_cards import (
    build_api_pull_url,
    build_rejection_card,
    clean_evidence_text,
    evidence_for_pr,
    filter_cards_with_human_comments,
    select_best_evidence,
)


class CleanEvidenceTextTests(unittest.TestCase):
    def test_clean_evidence_text_removes_markdown_noise_and_limits_length(self):
        text = "<!-- generated -->\n## Review\n\nThis should be fixed.\n\n```log\nvery long log\n```"

        cleaned = clean_evidence_text(text, max_length=25)

        self.assertEqual(cleaned, "Review This should be...")


class BuildApiPullUrlTests(unittest.TestCase):
    def test_build_api_pull_url_uses_repo_url_and_number(self):
        row = {
            "repo_url": "https://api.github.com/repos/example/project",
            "number": "42",
        }

        self.assertEqual(
            build_api_pull_url(row),
            "https://api.github.com/repos/example/project/pulls/42",
        )


class SelectBestEvidenceTests(unittest.TestCase):
    def test_select_best_evidence_prioritizes_changes_requested_review(self):
        evidences = [
            {
                "source": "pr_comment",
                "source_rank": 30,
                "body": "General human comment",
                "state": "COMMENTED",
                "user_type": "User",
            },
            {
                "source": "pr_review",
                "source_rank": 10,
                "body": "Please fix the behavior",
                "state": "CHANGES_REQUESTED",
                "user_type": "User",
            },
        ]

        best = select_best_evidence(evidences)

        self.assertEqual(best["source"], "pr_review")
        self.assertEqual(best["body"], "Please fix the behavior")

    def test_select_best_evidence_falls_back_to_pr_description(self):
        evidences = [
            {
                "source": "pull_request",
                "source_rank": 90,
                "body": "Title\n\nPR body",
                "state": "",
                "user_type": "",
            }
        ]

        best = select_best_evidence(evidences)

        self.assertEqual(best["source"], "pull_request")

    def test_committed_timeline_messages_are_not_used_as_rejection_evidence(self):
        pr = {
            "id": "123",
            "repo_url": "https://api.github.com/repos/example/project",
            "number": "42",
            "title": "Fix parser",
            "body": "Parser implementation",
        }
        indexes = {
            "timeline_by_pr_id": {
                "123": [
                    {
                        "event": "committed",
                        "message": "Initial implementation commit",
                        "actor": "dev",
                        "commit_id": "abc",
                    }
                ]
            }
        }

        best = select_best_evidence(evidence_for_pr(pr, indexes))

        self.assertEqual(best["source"], "pull_request")


class BuildRejectionCardTests(unittest.TestCase):
    def test_build_rejection_card_maps_required_fields(self):
        pr = {
            "id": "123",
            "repo_id": "9",
            "html_url": "https://github.com/example/project/pull/42",
            "agent": "Claude_Code",
            "language": "Python",
            "task_type": "fix",
            "created_at": "2025-01-01T00:00:00Z",
            "closed_at": "2025-01-02T00:00:00Z",
            "change_complexity_bin": "low",
            "repo_popularity_bin": "medium",
            "title": "Fix parser",
            "body": "Parser should handle spaces.",
            "commit_count": "2",
        }
        evidence = {
            "source": "pr_review",
            "source_rank": 10,
            "body": "Needs tests for whitespace.",
            "state": "CHANGES_REQUESTED",
            "user": "reviewer",
            "user_type": "User",
            "created_at": "2025-01-01T12:00:00Z",
            "id": "777",
        }

        card = build_rejection_card(pr, evidence, evidence_count=3)

        self.assertEqual(card["card_id"], "123-A")
        self.assertEqual(card["pr_id"], "123")
        self.assertEqual(card["review_state"], "CHANGES_REQUESTED")
        self.assertEqual(card["evidence_source"], "pr_review")
        self.assertEqual(card["evidence_text"], "Needs tests for whitespace.")
        self.assertEqual(card["needs_manual_context_check"], "false")
        self.assertEqual(card["population_case_type"], "rejected")
        self.assertEqual(card["pr_state"], "")
        self.assertEqual(card["merged"], "false")
        self.assertEqual(card["changes_requested_review_count"], "1")
        self.assertEqual(card["evidence_quality_score"], "8")
        self.assertEqual(card["discard_candidate_reason"], "")
        self.assertIn("Fix parser", card["context_summary"])

    def test_build_rejection_card_marks_missing_text_for_manual_check(self):
        pr = {"id": "123", "title": "Fix parser", "body": ""}
        evidence = {
            "source": "pull_request",
            "source_rank": 90,
            "body": "",
            "state": "",
            "user": "",
            "user_type": "",
        }

        card = build_rejection_card(pr, evidence, evidence_count=0)

        self.assertEqual(card["needs_manual_context_check"], "true")
        self.assertEqual(card["evidence_source"], "sin_evidencia_suficiente")


class FilterCardsWithHumanCommentsTests(unittest.TestCase):
    def test_filter_cards_with_human_comments_keeps_numeric_positive_counts(self):
        cards = [
            {"card_id": "1-A", "human_comment_count": "2"},
            {"card_id": "2-A", "human_comment_count": "0"},
            {"card_id": "3-A", "human_comment_count": ""},
        ]

        filtered = filter_cards_with_human_comments(cards)

        self.assertEqual([card["card_id"] for card in filtered], ["1-A"])


if __name__ == "__main__":
    unittest.main()
