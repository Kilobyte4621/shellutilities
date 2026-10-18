#!/usr/bin/env python3
"""Unit tests for wordlist_cleaner."""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

import wordlist_cleaner


class TestReplacementCharacter(unittest.TestCase):
    def test_replacement_character_rejected_by_default(self):
        self.assert_rejected(keep_all=False)

    def test_replacement_character_rejected_with_keep_all(self):
        self.assert_rejected(keep_all=True)

    def assert_rejected(self, keep_all):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "input.txt"
            destination = tmp_path / "output.txt"

            source.write_text(
                "apple\n"
                "\uFFFDholey\n"
                "caf\uFFFD\n"
                "banana\n",
                encoding="utf-8",
            )

            wordlist_cleaner.clean_wordlists(
                sources=[source],
                destination=destination,
                min_length=3,
                keep_all=keep_all,
            )

            words = destination.read_text(
                encoding="utf-8"
            ).splitlines()

            self.assertEqual(words, ["apple", "banana"])
            self.assertNotIn("\uFFFDholey", words)
            self.assertNotIn("caf\uFFFD", words)


if __name__ == "__main__":
    unittest.main()
