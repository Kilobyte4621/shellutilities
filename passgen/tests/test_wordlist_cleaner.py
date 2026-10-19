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


class TestWordFiltering(unittest.TestCase):
    def clean_words(self, entries, min_length=3):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "input.txt"
            destination = tmp_path / "output.txt"

            source.write_text(
                "\n".join(entries) + "\n",
                encoding="utf-8",
            )

            wordlist_cleaner.clean_wordlists(
                sources=[source],
                destination=destination,
                min_length=min_length,
            )

            return destination.read_text(
                encoding="utf-8"
            ).splitlines()

    def test_replacement_character_rejected(self):
        words = self.clean_words([
            "apple",
            "\uFFFDholey",
            "caf\uFFFD",
            "banana",
        ])

        self.assertEqual(words, ["apple", "banana"])

    def test_non_ascii_letters_rejected(self):
        words = self.clean_words([
            "apple",
            "café",
            "中文",
            "banana",
        ])

        self.assertEqual(words, ["apple", "banana"])

    def test_digits_and_symbols_rejected(self):
        words = self.clean_words([
            "apple",
            "hello123",
            "hello-world",
            "banana",
        ])

        self.assertEqual(words, ["apple", "banana"])

    def test_uppercase_normalized_to_lowercase(self):
        words = self.clean_words([
            "Apple",
            "BANANA",
            "Cherry",
        ])

        self.assertEqual(words, ["apple", "banana", "cherry"])

    def test_minimum_length_enforced(self):
        words = self.clean_words([
            "ant",
            "apple",
            "banana",
        ], min_length=5)

        self.assertEqual(words, ["apple", "banana"])

    def test_duplicates_removed_after_normalization(self):
        words = self.clean_words([
            "Apple",
            "apple",
            "APPLE",
            "banana",
        ])

        self.assertEqual(words, ["apple", "banana"])




if __name__ == "__main__":
    unittest.main()