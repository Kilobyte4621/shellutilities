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

    def test_modified_word_entropy_accounts_for_duplicate_outputs(self):
        alphabet = "e" + chr(0x0301)

        entropy = passgen.modified_word_entropy("e", alphabet)

        self.assertAlmostEqual(entropy, 1.5, places=12)



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

    def test_insertion_with_combining_mark_returns_nfc(self):
        import unicodedata

        with (
            patch("passgen.secrets.randbelow", return_value=1),
            patch("passgen.secrets.choice", return_value="\u0301"),
        ):
            result = passgen.insert_random_character("café", "\u0301")

        self.assertEqual(result, "ćafé")
        self.assertTrue(unicodedata.is_normalized("NFC", result))    


    def test_insertion_with_noncomposable_combining_mark(self):
        import unicodedata

        overlay = chr(0x0338)

        with (
            patch("passgen.secrets.randbelow", return_value=1),
            patch("passgen.secrets.choice", return_value=overlay),
        ):
            result = passgen.insert_random_character("a", overlay)

        self.assertEqual(result, "a" + overlay)
        self.assertEqual(len(result), 2)
        self.assertTrue(unicodedata.is_normalized("NFC", result))

    def test_insertion_can_split_emoji_grapheme_cluster(self):
        family = "👨‍👩‍👧‍👦"

        with (
            patch("passgen.secrets.randbelow", return_value=1),
            patch("passgen.secrets.choice", return_value="X"),
        ):
            result = passgen.insert_random_character(family, "X")

        self.assertEqual(result, "👨X‍👩‍👧‍👦")
        self.assertEqual(len(result), len(family) + 1)


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

    def test_modified_word_entropy_normalizes_unicode_input(self):
        composed = "café"
        decomposed = "cafe" + chr(0x0301)
        accent = chr(0x0301)

        self.assertTrue(
            math.isclose(
                passgen.modified_word_entropy(composed, accent),
                passgen.modified_word_entropy(decomposed, accent),
                rel_tol=0,
                abs_tol=1e-12,
            )
        )

    def test_modified_word_entropy_with_combining_mark(self):
        accent = chr(0x0301)
        entropy = passgen.modified_word_entropy("café", accent)

        self.assertTrue(
            math.isclose(entropy, math.log2(5), abs_tol=1e-12)
        )

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

    def test_wordlist_normalizes_unicode_and_preserves_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "words.txt"
            path.write_text(
                "\n".join([
                    "café",
                    "cafe" + chr(0x0301),
                    "Casa",
                    "casa",
                    "ação",
                ]) + "\n",
                encoding="utf-8",
            )

            words = passgen.load_wordlist(path)

        self.assertEqual(words, ["café", "Casa", "casa", "ação"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
