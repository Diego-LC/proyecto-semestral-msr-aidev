import unittest


from exploration.aidev.sampling.stratified_sampler import (
    DEFAULT_FALLBACK_STRATA_FIELDS,
    DEFAULT_POPULATION_MODE,
    DEFAULT_STRATA_FIELDS,
    POPULATION_MERGED_AFTER_REWORK,
    allocate_stratified_quotas,
    build_stratum_key,
    choose_supported_strata_fields,
    collapse_rare_values,
    filter_population_prs,
    filter_rejected_prs,
    has_field_in_candidates,
    is_reworked_merged_pr,
    population_mode_includes_reworked_merged,
    stratified_sample,
    unique_candidates,
)


class FilterRejectedPrsTests(unittest.TestCase):
    def test_filter_rejected_prs_keeps_closed_prs_without_merge(self):
        rows = [
            {"id": 1, "state": "closed", "merged_at": None},
            {"id": 2, "state": "closed", "merged_at": ""},
            {"id": 3, "state": "closed", "merged_at": "2025-07-01T00:00:00Z"},
            {"id": 4, "state": "open", "merged_at": None},
        ]

        rejected = filter_rejected_prs(rows)

        self.assertEqual([row["id"] for row in rejected], [1, 2])


class StratumKeyTests(unittest.TestCase):
    def test_default_strata_use_agent_only(self):
        self.assertEqual(DEFAULT_STRATA_FIELDS, ["agent"])
        self.assertEqual(DEFAULT_FALLBACK_STRATA_FIELDS, ["agent"])

    def test_default_population_uses_merged_after_rework(self):
        self.assertEqual(DEFAULT_POPULATION_MODE, POPULATION_MERGED_AFTER_REWORK)

    def test_build_stratum_key_normalizes_missing_values(self):
        row = {"agent": "Claude_Code", "language": None, "change_complexity_bin": ""}

        key = build_stratum_key(row, ["agent", "change_complexity_bin"])

        self.assertEqual(key, "Claude_Code|unknown")


class PopulationFilterTests(unittest.TestCase):
    def test_reworked_merged_pr_requires_merge_code_change_and_feedback(self):
        self.assertTrue(
            is_reworked_merged_pr(
                {
                    "state": "closed",
                    "merged_at": "2025-07-01T00:00:00Z",
                    "commit_count": 2,
                    "changes_requested_review_count": 1,
                }
            )
        )
        self.assertFalse(
            is_reworked_merged_pr(
                {
                    "state": "closed",
                    "merged_at": "2025-07-01T00:00:00Z",
                    "commit_count": 1,
                    "changes_requested_review_count": 1,
                }
            )
        )

    def test_population_filter_can_include_reworked_merged_prs(self):
        rows = [
            {"id": 1, "state": "closed", "merged_at": ""},
            {
                "id": 2,
                "state": "closed",
                "merged_at": "2025-07-01T00:00:00Z",
                "commit_count": 3,
                "human_review_count": 1,
            },
            {"id": 3, "state": "open", "merged_at": ""},
        ]

        population = filter_population_prs(rows, "rejected-or-reworked-merged")

        self.assertEqual([row["id"] for row in population], [1, 2])
        self.assertEqual(
            [row["population_case_type"] for row in population],
            ["rejected", "merged_after_rework"],
        )

    def test_population_filter_can_select_only_not_immediately_accepted_prs(self):
        rows = [
            {"id": 1, "state": "closed", "merged_at": ""},
            {
                "id": 2,
                "state": "closed",
                "merged_at": "2025-07-01T00:00:00Z",
                "commit_count": 3,
                "human_review_count": 1,
            },
        ]

        population = filter_population_prs(rows, "not-immediately-accepted")

        self.assertEqual([row["id"] for row in population], [2])
        self.assertEqual(population[0]["population_case_type"], "merged_after_rework")
        self.assertEqual(population[0]["merged"], "true")

    def test_population_mode_detects_reworked_merged_modes(self):
        self.assertTrue(population_mode_includes_reworked_merged("merged-after-rework"))
        self.assertTrue(population_mode_includes_reworked_merged("not-immediately-accepted"))
        self.assertFalse(population_mode_includes_reworked_merged("rejected"))


class QuotaAllocationTests(unittest.TestCase):
    def test_allocate_stratified_quotas_uses_proportions_and_minimum(self):
        sizes = {
            "Claude_Code|low": 80,
            "Codex|high": 20,
        }

        quotas = allocate_stratified_quotas(sizes, target_size=10, min_per_stratum=2)

        self.assertEqual(
            quotas,
            {
                "Claude_Code|low": 8,
                "Codex|high": 2,
            },
        )

    def test_allocate_stratified_quotas_caps_quota_at_stratum_size(self):
        sizes = {
            "large": 100,
            "tiny": 1,
        }

        quotas = allocate_stratified_quotas(sizes, target_size=10, min_per_stratum=3)

        self.assertEqual(quotas["tiny"], 1)
        self.assertEqual(sum(quotas.values()), 10)

    def test_allocate_stratified_quotas_rejects_impossible_minimum(self):
        sizes = {"a": 10, "b": 10, "c": 10}

        with self.assertRaises(ValueError):
            allocate_stratified_quotas(sizes, target_size=2, min_per_stratum=1)


class SamplingTests(unittest.TestCase):
    def test_collapse_rare_values_keeps_top_categories_and_groups_the_rest(self):
        rows = [
            {"language": "Python"},
            {"language": "Python"},
            {"language": "Rust"},
            {"language": "Rust"},
            {"language": "Go"},
            {"language": ""},
        ]

        collapsed = collapse_rare_values(rows, field="language", max_values=2)

        self.assertEqual(
            [row["language"] for row in collapsed],
            ["Python", "Python", "Rust", "Rust", "other", "unknown"],
        )

    def test_stratified_sample_is_reproducible_and_tracks_metadata(self):
        rows = [
            {"id": idx, "agent": "A", "language": "Python", "change_complexity_bin": "low"}
            for idx in range(10)
        ] + [
            {"id": 100 + idx, "agent": "B", "language": "Rust", "change_complexity_bin": "high"}
            for idx in range(10)
        ]

        first = stratified_sample(
            rows,
            strata_fields=["agent"],
            target_size=6,
            min_per_stratum=2,
            seed=20260510,
        )
        second = stratified_sample(
            rows,
            strata_fields=["agent"],
            target_size=6,
            min_per_stratum=2,
            seed=20260510,
        )

        self.assertEqual([row["id"] for row in first.rows], [row["id"] for row in second.rows])
        self.assertEqual(len(first.rows), 6)
        self.assertEqual(set(first.quotas.values()), {3})
        self.assertTrue(all("_stratum_key" in row for row in first.rows))

    def test_choose_supported_strata_fields_falls_back_when_main_fields_are_too_many(self):
        rows = [
            {
                "agent": "agent-a" if idx < 3 else "agent-b",
                "language": f"language-{idx}",
                "change_complexity_bin": "low",
                "created_period": "recent",
            }
            for idx in range(5)
        ]
        candidates = [
            ["agent", "language", "change_complexity_bin", "created_period"],
            ["agent", "change_complexity_bin"],
        ]

        chosen = choose_supported_strata_fields(
            rows,
            candidates=candidates,
            target_size=6,
            min_per_stratum=2,
        )

        self.assertEqual(chosen, ["agent", "change_complexity_bin"])

    def test_has_field_in_candidates_detects_language_only_when_requested(self):
        self.assertFalse(
            has_field_in_candidates(
                [["agent", "change_complexity_bin"], ["agent"]],
                "language",
            )
        )
        self.assertTrue(
            has_field_in_candidates(
                [["agent", "language"], ["agent"]],
                "language",
            )
        )

    def test_unique_candidates_removes_duplicate_fallbacks(self):
        self.assertEqual(
            unique_candidates([["agent"], ["agent"], ["agent", "change_complexity_bin"]]),
            [["agent"], ["agent", "change_complexity_bin"]],
        )


if __name__ == "__main__":
    unittest.main()
