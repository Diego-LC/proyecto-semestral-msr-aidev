import unittest


from exploration.aidev.labeling_machine.labeling_machine_adapter import (
    ARTIFACT_FIELDS,
    LABELING_FIELDS,
    build_labeling_schema,
    normalize_card_for_labeling,
    validate_cards_for_labeling,
)


class NormalizeCardForLabelingTests(unittest.TestCase):
    def test_normalize_card_for_labeling_adds_sequential_artifact_id_and_blank_labels(self):
        card = {
            "card_id": "2888185420-A",
            "pr_id": "2888185420",
            "repo_id": "514553345",
            "html_url": "https://github.com/SoftFever/OrcaSlicer/pull/8624",
            "agent": "Claude_Code",
            "language": "C++",
            "task_type": "feat",
            "created_at": "2025-02-28T22:44:18Z",
            "closed_at": "2025-02-28T22:44:56Z",
            "complexity_bin": "high",
            "repo_popularity_bin": "high",
            "review_state": "COMMENTED",
            "evidence_text": "I intended to open a PR for my own fork.",
            "evidence_source": "pr_comment",
            "context_summary": "Title: No-switching-tab-on-slice",
            "needs_manual_context_check": "false",
            "evidence_user": "kennethjiang",
            "evidence_user_type": "User",
            "evidence_created_at": "2025-02-28T22:45:57Z",
            "evidence_id": "2691672195",
            "evidence_count": "2",
            "commit_count": "30",
        }

        row = normalize_card_for_labeling(card, artifact_id=7)

        self.assertEqual(row["artifact_id"], "7")
        self.assertEqual(row["card_id"], "2888185420-A")
        self.assertEqual(row["evidence_text"], "I intended to open a PR for my own fork.")
        self.assertEqual(row["category_parent"], "")
        self.assertEqual(row["subcategory"], "")
        self.assertEqual(row["confidence"], "")
        self.assertEqual(row["rationale"], "")
        self.assertEqual(row["needs_discussion"], "")
        self.assertEqual(row["duration_sec"], "")
        self.assertEqual(set(ARTIFACT_FIELDS + LABELING_FIELDS), set(row.keys()))


class ValidateCardsForLabelingTests(unittest.TestCase):
    def test_validate_cards_for_labeling_rejects_missing_evidence_text(self):
        cards = [
            {
                "card_id": "1-A",
                "pr_id": "1",
                "html_url": "https://github.com/example/project/pull/1",
                "evidence_text": "",
                "context_summary": "Title: Fix bug",
            }
        ]

        with self.assertRaises(ValueError) as context:
            validate_cards_for_labeling(cards)

        self.assertIn("evidence_text", str(context.exception))

    def test_validate_cards_for_labeling_rejects_duplicate_card_id(self):
        cards = [
            {
                "card_id": "1-A",
                "pr_id": "1",
                "html_url": "https://github.com/example/project/pull/1",
                "evidence_text": "Needs tests.",
                "context_summary": "Title: Fix bug",
            },
            {
                "card_id": "1-A",
                "pr_id": "1",
                "html_url": "https://github.com/example/project/pull/1",
                "evidence_text": "Needs tests.",
                "context_summary": "Title: Fix bug",
            },
        ]

        with self.assertRaises(ValueError) as context:
            validate_cards_for_labeling(cards)

        self.assertIn("duplicated card_id", str(context.exception))


class BuildLabelingSchemaTests(unittest.TestCase):
    def test_build_labeling_schema_documents_artifact_and_labeling_fields(self):
        schema = build_labeling_schema(row_count=150)

        self.assertEqual(schema["row_count"], 150)
        self.assertIn("evidence_text", schema["artifact_fields"])
        self.assertIn("category_parent", schema["labeling_fields"])
        self.assertIn("Cohen", schema["validation_notes"])


if __name__ == "__main__":
    unittest.main()
