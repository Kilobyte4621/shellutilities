#!/usr/bin/env python3
"""Unit tests for passgen."""

import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

import passgen


class TestInsertion(unittest.TestCase):

    def test_inserts_exactly_one_character(self):
        original = "cavalo"

        with (
            patch("passgen.secrets.randbelow", return_value=3),
            patch("passgen.secrets.choice", return_value="#"),
        ):
            result = passgen.insert_random_character(
                original,
                "#",
            )

        self.assertEqual(result, "cav#alo")
        self.assertEqual(len(result), len(original) + 1)
        self.assertEqual(result.replace("#", "", 1), original)

    def test_insertion_at_start(self):
        with (
            patch("passgen.secrets.randbelow", return_value=0),
            patch("passgen.secrets.choice", return_value="X"),
        ):
            result = passgen.insert_random_character("word", "X")

        self.assertEqual(result, "Xword")

    def test_insertion_at_end(self):
        with (
            patch("passgen.secrets.randbelow", return_value=4),
            patch("passgen.secrets.choice", return_value="X"),
        ):
            result = passgen.insert_random_character("word", "X")

        self.assertEqual(result, "wordX")


class TestEntropy(unittest.TestCase):

    def test_generation_choice_entropy_formula(self):
        words = ["a", "abcd"]
        word_count = 2
        random_count = 1
        alphabet_size = 2

        expected = (
            2 * math.log2(2)
            + math.log2(math.comb(2, 1))
            + math.log2(2)
            + (
                math.log2(len("a") + 1)
                + math.log2(len("abcd") + 1)
            ) / 2
        )

        actual = passgen.generation_choice_entropy(
            words,
            word_count,
            random_count,
            alphabet_size,
        )

        self.assertAlmostEqual(actual, expected, places=12)

    def test_entropy_without_insertions(self):
        words = ["alpha", "bravo", "charlie", "delta"]

        actual = passgen.generation_choice_entropy(
            words,
            3,
            0,
            10,
        )

        self.assertAlmostEqual(actual, 6.0, places=12)

    def test_target_word_count_meets_entropy(self):
        words = ["alpha", "bravo", "charlie", "delta"]
        target = 15
        random_count = 1
        alphabet_size = 10

        count = passgen.required_word_count(
            words,
            target,
            random_count,
            alphabet_size,
        )

        actual = passgen.generation_choice_entropy(
            words,
            count,
            random_count,
            alphabet_size,
        )

        self.assertGreaterEqual(actual, target)

        if count > random_count:
            previous = passgen.generation_choice_entropy(
                words,
                count - 1,
                random_count,
                alphabet_size,
            )
            self.assertLess(previous, target)


class TestArguments(unittest.TestCase):

    def test_random_count_exceeds_word_count(self):
        with self.assertRaisesRegex(ValueError, "-R cannot exceed"):
            passgen.parse_args(["-p", "2", "-R", "3"])

    def test_negative_random_count(self):
        with self.assertRaisesRegex(ValueError, "-R"):
            passgen.parse_args(["-p", "2", "-R", "-1"])

    def test_duplicate_random_count(self):
        with self.assertRaisesRegex(ValueError, "Duplicate -R"):
            passgen.parse_args(
                ["-p", "3", "-R", "1", "-R", "2"]
            )

    def test_random_count_requires_passphrase_mode(self):
        with self.assertRaisesRegex(ValueError, "requires -p"):
            passgen.parse_args(["-R", "1"])


class TestWordlist(unittest.TestCase):

    def test_load_wordlist_removes_duplicates_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.txt"
            path.write_text(
                "alpha\nbravo\nalpha\n\ncharlie\n",
                encoding="utf-8",
            )

            self.assertEqual(
                passgen.load_wordlist(path),
                ["alpha", "bravo", "charlie"],
            )

    def test_wordlist_requires_two_distinct_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.txt"
            path.write_text(
                "alpha\nalpha\n\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "at least two distinct words",
            ):
                passgen.load_wordlist(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
