import unittest

from app.main import _life_course_temporal_coverage


class LifeCourseTemporalCoverageTests(unittest.TestCase):
    def test_reports_gap_between_world_day_and_latest_record(self):
        coverage = _life_course_temporal_coverage(26, 22, from_day=20, to_day=26)
        self.assertEqual(coverage["current_day"], 26)
        self.assertEqual(coverage["latest_recorded_day"], 22)
        self.assertEqual(coverage["days_without_records_after_latest"], 4)
        self.assertFalse(coverage["has_current_day_record"])
        self.assertTrue(coverage["window_includes_current_day"])

    def test_current_day_record_has_no_gap(self):
        coverage = _life_course_temporal_coverage(26, 26, from_day=20, to_day=26)
        self.assertTrue(coverage["has_current_day_record"])
        self.assertEqual(coverage["days_without_records_after_latest"], 0)

    def test_archive_window_does_not_claim_to_show_current_day(self):
        coverage = _life_course_temporal_coverage(26, 22, from_day=16, to_day=22)
        self.assertFalse(coverage["window_includes_current_day"])

    def test_agent_without_records_uses_explicit_none(self):
        coverage = _life_course_temporal_coverage(26, None, from_day=20, to_day=26)
        self.assertIsNone(coverage["latest_recorded_day"])
        self.assertIsNone(coverage["days_without_records_after_latest"])
        self.assertFalse(coverage["has_current_day_record"])


if __name__ == "__main__":
    unittest.main()
