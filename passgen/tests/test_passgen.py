#!/usr/bin/env python3
"""Unit tests for passgen."""

import io
import itertools
import math
import regex
import sys
import tempfile
import unicodedata
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

import passgen
import wordlist_cleaner



class TestInsertion(unittest.TestCase):

    def test_modified_word_entropy_matches_exhaustive_distribution(self):
        words = [
            "",
            "a",
            "é",
            "ee",
            "café",
            "a\u0301",
            "\u0301",
            "\u0338",
            "👨‍👩‍👧‍👦",
        ]

        alphabets = [
            "a",
            "ab",
            "aa",
            "e",
            "é",
            "\u0301",
            "\u0338",
            "e\u0301",
            "a\u0301",
            "X\u0301",
            "👩",
        ]

        def entropy(outputs):
            counts = Counter(outputs)
            total = len(outputs)
            return -sum(
                (count / total) * math.log2(count / total)
                for count in counts.values()
            )

        cases = 0

        for original_word in words:
            word = unicodedata.normalize("NFC", original_word)

            for alphabet in alphabets:
                outputs = []
                clusters = regex.findall(r"\X", word)

                for position in range(len(clusters) + 1):
                    for character in alphabet:
                        with (
                            patch(
                                "passgen.secrets.randbelow",
                                return_value=position,
                            ),
                            patch(
                                "passgen.secrets.choice",
                                return_value=character,
                            ),
                        ):
                            outputs.append(
                                passgen.insert_random_character(
                                    word, alphabet
                                )
                            )

                expected = entropy(outputs)
                actual = passgen.modified_word_entropy(word, alphabet)

                self.assertAlmostEqual(
                    actual,
                    expected,
                    places=12,
                    msg=(
                        f"word={word!r}, alphabet={alphabet!r}, "
                        f"expected={expected}, actual={actual}"
                    ),
                )
                cases += 1

        self.assertEqual(cases, len(words) * len(alphabets))



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

    def test_insertion_preserves_emoji_grapheme_cluster(self):
        family = "👨‍👩‍👧‍👦"

        with (
            patch("passgen.secrets.randbelow", return_value=1),
            patch("passgen.secrets.choice", return_value="X"),
        ):
            result = passgen.insert_random_character(family, "X")

        self.assertEqual(result, "👨‍👩‍👧‍👦X")
        self.assertEqual(len(result), len(family) + 1)

    def test_insertion_respects_all_grapheme_boundaries(self):
        cases = [
            ("a\u0301", ["a\u0301"]),
            ("👍🏽", ["👍🏽"]),
            ("👨‍👩‍👧‍👦", ["👨‍👩‍👧‍👦"]),
            ("🇧🇷", ["🇧🇷"]),
            ("café", ["c", "a", "f", "é"]),
        ]

        for word, expected_clusters in cases:
            with self.subTest(word=word):
                clusters = regex.findall(r"\X", word)
                self.assertEqual(clusters, expected_clusters)

                for position in range(len(clusters) + 1):
                    with self.subTest(position=position):
                        with (
                            patch(
                                "passgen.secrets.randbelow",
                                return_value=position,
                            ),
                            patch(
                                "passgen.secrets.choice",
                                return_value="#",
                            ),
                        ):
                            result = passgen.insert_random_character(
                                word, "#"
                            )

                        expected = (
                            "".join(clusters[:position])
                            + "#"
                            + "".join(clusters[position:])
                        )
                        expected = unicodedata.normalize("NFC", expected)

                        self.assertEqual(result, expected)


class TestEntropy(unittest.TestCase):

    def test_complete_passphrase_entropy_by_exhaustive_enumeration(self):
        words = ["e", "x"]
        alphabet = "e\u0301"
        separator = "-"
        word_count = 2
        random_count = 1

        output_counts = Counter()
        total_paths = 0

        # Enumera as escolhas de palavras, a posição modificada,
        # a posição de inserção e o caractere inserido.
        for selected_words in itertools.product(
            words, repeat=word_count
        ):
            for (modified_index,) in itertools.combinations(
                range(word_count), random_count
            ):
                word = selected_words[modified_index]

                for position in range(len(word) + 1):
                    for character in alphabet:
                        modified = unicodedata.normalize(
                            "NFC",
                            word[:position] + character + word[position:],
                        )

                        output_words = list(selected_words)
                        output_words[modified_index] = modified
                        output = separator.join(output_words)

                        output_counts[output] += 1
                        total_paths += 1

        # Todas as palavras têm o mesmo comprimento, portanto
        # os 32 caminhos enumerados têm a mesma probabilidade.
        self.assertEqual(total_paths, 32)

        output_entropy = -sum(
            (count / total_paths) * math.log2(count / total_paths)
            for count in output_counts.values()
        )

        choice_entropy = passgen.generation_choice_entropy(
            words,
            word_count,
            random_count,
            len(alphabet),
        )

        self.assertAlmostEqual(output_entropy, 4.75)
        self.assertAlmostEqual(choice_entropy, 5.0)
        self.assertLess(output_entropy, choice_entropy)


    def test_generation_choice_entropy_can_exceed_output_entropy(self):
        words = ["e", "x"]
        alphabet = "e\u0301"

        choice_entropy = passgen.generation_choice_entropy(
            words, 1, 1, len(alphabet)
        )
        output_entropy = passgen.passphrase_position_entropy(
            words, alphabet, 1.0
        )

        self.assertAlmostEqual(choice_entropy, 3.0, places=12)
        self.assertAlmostEqual(output_entropy, 2.75, places=12)
        self.assertGreater(choice_entropy, output_entropy)

    def test_passphrase_position_entropy_normalizes_unicode_outputs(self):
        alphabet = "e\u0301"

        actual = passgen.passphrase_position_entropy(
            ["e", "x"], alphabet, 1.0
        )

        self.assertAlmostEqual(actual, 2.75, places=12)


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

    def test_nfc_collisions_reduce_final_output_entropy(self):
        words = ["e", "x"]
        alphabet = "e\u0301"

        output_counts = Counter()
        total_paths = 0

        for word in words:
            for position in range(len(word) + 1):
                for character in alphabet:
                    output = unicodedata.normalize(
                        "NFC",
                        word[:position] + character + word[position:],
                    )
                    output_counts[output] += 1
                    total_paths += 1

        output_entropy = -sum(
            (count / total_paths) * math.log2(count / total_paths)
            for count in output_counts.values()
        )

        choice_entropy = passgen.generation_choice_entropy(
            words,
            word_count=1,
            random_count=1,
            alphabet_size=len(alphabet),
        )

        self.assertEqual(total_paths, 8)
        self.assertEqual(len(output_counts), 7)
        self.assertAlmostEqual(output_entropy, 2.75)
        self.assertAlmostEqual(choice_entropy, 3.0)
        self.assertGreater(choice_entropy, output_entropy)

    def test_required_word_count_targets_choice_entropy(self):
        words = ["e", "x"]
        target = 3.0
        random_count = 1
        alphabet_size = 2

        count = passgen.required_word_count(
            words,
            target,
            random_count,
            alphabet_size,
        )

        choice_entropy = passgen.generation_choice_entropy(
            words,
            count,
            random_count,
            alphabet_size,
        )

        self.assertGreaterEqual(choice_entropy, target)

        if count > random_count:
            previous_entropy = passgen.generation_choice_entropy(
                words,
                count - 1,
                random_count,
                alphabet_size,
            )
            self.assertLess(previous_entropy, target)


    def test_passphrase_reports_generation_choice_entropy(self):
        words = ["alpha", "bravo"]

        for random_count in (0, 1):
            with self.subTest(random_count=random_count):
                options = {
                    "wordlist_path": "unused.txt",
                    "word_count": 2,
                    "target_entropy": None,
                    "random_count": random_count,
                    "separator": "-",
                }

                stderr = io.StringIO()
                expected_entropy = passgen.generation_choice_entropy(
                    words,
                    word_count=2,
                    random_count=random_count,
                    alphabet_size=len(
                        passgen.get_insertion_alphabet(options["separator"])
                    ),
                )

                with (
                    patch("passgen.load_wordlist", return_value=words),
                    patch(
                        "passgen.secrets.choice",
                        side_effect=["alpha", "bravo"],
                    ),
                    patch("passgen.secrets.SystemRandom") as mock_random,
                    patch(
                        "passgen.insert_random_character",
                        return_value="a1pha",
                    ),
                    patch("sys.stderr", stderr),
                    patch("sys.stdout", io.StringIO()),
                ):
                    mock_random.return_value.sample.side_effect = (
                        lambda population, count: list(population)[:count]
                    )
                    passgen.generate_passphrase(options)

                report = stderr.getvalue()
                self.assertIn("Generation-choice entropy:", report)
                self.assertIn(
                    f"Generation-choice entropy: {expected_entropy:.2f} bits",
                    report,
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

    
    def test_wordlist_normalizes_unicode_and_removes_duplicates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "words.txt"
            path.write_text(
                "\n".join([
                    "café",
                    "cafe" + chr(0x0301),
                    "casa",
                    "ação",
                ]) + "\n",
                encoding="utf-8",
            )

            words = passgen.load_wordlist(path)

        self.assertEqual(words, ["café", "casa", "ação"])


    def test_generate_passphrase_rejects_words_containing_separator(self):
        words = ["alpha", "bravo", "char-lie"]
        options = {
            "wordlist_path": "unused.txt",
            "word_count": 2,
            "target_entropy": None,
            "random_count": 0,
            "separator": "-",
        }

        with (
            patch("passgen.load_wordlist", return_value=words),
            patch("sys.stdout", io.StringIO()),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "selected separator",
            ):
                passgen.generate_passphrase(options)

    def test_generate_passphrase_accepts_words_without_separator(self):
        words = ["alpha", "bravo"]
        options = {
            "wordlist_path": "unused.txt",
            "word_count": 2,
            "target_entropy": None,
            "random_count": 0,
            "separator": " ",
        }

        with (
            patch("passgen.load_wordlist", return_value=words),
            patch(
                "passgen.secrets.choice",
                side_effect=words,
            ),
            patch("sys.stdout", io.StringIO()) as stdout,
            patch("sys.stderr", io.StringIO()),
        ):
            passgen.generate_passphrase(options)

        self.assertEqual(stdout.getvalue().strip(), "alpha bravo")



class TestWordlistSimilarity(unittest.TestCase):

    @staticmethod
    def reference_levenshtein(first, second):
        """Independent reference implementation."""
        previous = list(range(len(second) + 1))

        for i, char_first in enumerate(first, start=1):
            current = [i]

            for j, char_second in enumerate(second, start=1):
                current.append(
                    min(
                        current[j - 1] + 1,
                        previous[j] + 1,
                        previous[j - 1]
                        + (char_first != char_second),
                    )
                )

            previous = current

        return previous[-1]

    @classmethod
    def reference_filter(cls, words, max_distance=2):
        """Exhaustive reference without the signature index."""
        words = sorted(words)
        parent = list(range(len(words)))

        def find(index):
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        def union(first, second):
            root_first = find(first)
            root_second = find(second)

            if root_first != root_second:
                parent[root_second] = root_first

        for index, word in enumerate(words):
            for other_index in range(index):
                other = words[other_index]

                threshold = (
                    1
                    if max(len(word), len(other)) <= 5
                    else max_distance
                )

                if abs(len(word) - len(other)) > threshold:
                    continue

                if (
                    cls.reference_levenshtein(word, other)
                    <= threshold
                ):
                    union(index, other_index)

        representatives = {}

        for index, word in enumerate(words):
            root = find(index)
            current = representatives.get(root)

            if current is None or (len(word), word) < (
                len(current), current
            ):
                representatives[root] = word

        return sorted(representatives.values())

    def test_levenshtein_known_distances(self):
        cases = [
            ("", "", 0),
            ("cat", "cat", 0),
            ("cat", "cot", 1),       # Substitution
            ("cat", "cats", 1),      # Insertion
            ("cats", "cat", 1),      # Deletion
            ("kitten", "sitting", 3),
            ("book", "back", 2),
            ("casa", "caas", 2),     # Transposition costs two
            ("café", "cafe", 1),
            ("abc", "", 3),
        ]

        for first, second, expected in cases:
            with self.subTest(first=first, second=second):
                self.assertEqual(
                    wordlist_cleaner.levenshtein_distance(
                        first, second
                    ),
                    expected,
                )

                self.assertEqual(
                    self.reference_levenshtein(first, second),
                    expected,
                )

    def test_reference_distance_is_symmetric(self):
        words = [
            "", "a", "ab", "abc", "casa",
            "caas", "kitten", "sitting", "café",
        ]

        for first in words:
            for second in words:
                with self.subTest(first=first, second=second):
                    forward = self.reference_levenshtein(
                        first, second
                    )
                    backward = self.reference_levenshtein(
                        second, first
                    )

                    self.assertEqual(forward, backward)

    def test_known_similar_words_are_grouped(self):
        words = [
            "cat",
            "cot",
            "coat",
            "quartz",
            "quarts",
            "quarxx",
            "planet",
            "planets",
        ]

        result = wordlist_cleaner.filter_memorable_words(
            words, max_distance=2
        )

        self.assertEqual(
            result,
            self.reference_filter(words, max_distance=2),
        )

        self.assertEqual(result, sorted(result))

    def test_transitive_grouping(self):
        # cat and coat are distance 2 apart, but both connect
        # through cot under the short-word threshold of 1.
        words = ["cat", "cot", "coat"]

        result = wordlist_cleaner.filter_memorable_words(
            words, max_distance=2
        )

        self.assertEqual(result, ["cat"])

    def test_distant_words_are_preserved(self):
        words = ["alpha", "quartz", "window", "zebra"]

        result = wordlist_cleaner.filter_memorable_words(
            words, max_distance=2
        )

        self.assertEqual(result, sorted(words))

    def test_duplicate_words_are_collapsed(self):
        words = ["alpha", "alpha", "bravo", "bravo"]

        result = wordlist_cleaner.filter_memorable_words(words)

        self.assertEqual(result, ["alpha", "bravo"])

    def test_empty_and_single_word_lists(self):
        self.assertEqual(
            wordlist_cleaner.filter_memorable_words([]),
            [],
        )

        self.assertEqual(
            wordlist_cleaner.filter_memorable_words(["alpha"]),
            ["alpha"],
        )

    def test_short_word_threshold_is_one(self):
        # Both words are short; distance 2 must not group them.
        words = ["book", "back"]

        result = wordlist_cleaner.filter_memorable_words(
            words, max_distance=2
        )

        self.assertEqual(result, ["back", "book"])

    def test_long_word_threshold_is_two(self):
        # Two substitutions: accepted for words longer than five.
        words = ["quartz", "quarxx"]

        result = wordlist_cleaner.filter_memorable_words(
            words, max_distance=2
        )

        self.assertEqual(result, ["quartz"])

    def test_fast_filter_matches_exhaustive_reference(self):
        # Broad alphabet and mixed lengths produce less artificial
        # similarity than an alphabet containing only a and b.
        alphabet = "abcdefghijkmnopqrstuvwxyz"
        words = {
            "cat", "cot", "coat", "quartz", "quarts",
            "quarxx", "planet", "planets", "alpha",
            "bravo", "charlie", "delta", "epsilon",
        }

        # Deterministic synthetic inputs; no external dependencies.
        import random

        rng = random.Random(20261017)

        for _ in range(180):
            length = rng.randint(3, 10)
            words.add(
                "".join(rng.choices(alphabet, k=length))
            )

        words = sorted(words)

        actual = wordlist_cleaner.filter_memorable_words(
            words, max_distance=2
        )
        expected = self.reference_filter(
            words, max_distance=2
        )

        self.assertEqual(
            actual,
            expected,
            msg=(
                "Optimized filter differs from exhaustive reference.\n"
                f"Actual: {actual}\n"
                f"Expected: {expected}"
            ),
        )

    def test_exhaustive_small_alphabet_matches_reference(self):
        # Exhaustively compare every word over {a,b,c} up to length 4.
        words = {
            "".join(chars)
            for length in range(1, 5)
            for chars in itertools.product("abc", repeat=length)
        }

        actual = wordlist_cleaner.filter_memorable_words(
            sorted(words), max_distance=2
        )
        expected = self.reference_filter(
            sorted(words), max_distance=2
        )

        self.assertEqual(actual, expected)



if __name__ == "__main__":
    unittest.main(verbosity=2)
