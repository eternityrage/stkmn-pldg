"""Focused test: YouTube publishes at most 3x/week (Mon/Wed/Fri UTC).

Uses only the standard library. Run from the repo root:
    python -m unittest discover -s tests -v
"""
import datetime
import os
import unittest

import daily_publisher


class TestYoutubeSchedule(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.pop("ENABLE_YOUTUBE", None)

    def tearDown(self):
        if self._old is None:
            os.environ.pop("ENABLE_YOUTUBE", None)
        else:
            os.environ["ENABLE_YOUTUBE"] = self._old

    def test_explicit_flag_true_values_enable(self):
        for value in ("true", "True", "1", "yes", "on"):
            with self.subTest(value=value):
                os.environ["ENABLE_YOUTUBE"] = value
                self.assertTrue(daily_publisher.should_upload_youtube_today())

    def test_explicit_flag_false_values_skip(self):
        for value in ("false", "False", "0", "no", "off", ""):
            with self.subTest(value=value):
                os.environ["ENABLE_YOUTUBE"] = value
                self.assertFalse(daily_publisher.should_upload_youtube_today())

    def test_unset_flag_follows_mon_wed_fri_rule(self):
        # No ENABLE_YOUTUBE (e.g. local run): only Mon/Wed/Fri UTC.
        os.environ.pop("ENABLE_YOUTUBE", None)
        expected = datetime.datetime.now(datetime.timezone.utc).weekday() in (0, 2, 4)
        self.assertEqual(daily_publisher.should_upload_youtube_today(), expected)


if __name__ == "__main__":
    unittest.main()
