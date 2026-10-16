#!/usr/bin/env python3
"""Cryptographically secure password and passphrase generator."""

import itertools
import math
import secrets
import string
import sys
from pathlib import Path

CLASSES = {
    "a": string.ascii_lowercase,
    "A": string.ascii_uppercase,
    "0": string.digits,
    "!": "!@#$%^&*()-_=+[]{}:,.?/",
}

MAX_LENGTH = 4096
DEFAULT_WORDLIST = Path(__file__).resolve().with_name("wordlist.csv")


def usage():
    print("""Usage:
  passgen CHAR_CLASSES (-L LENGTH | -E BITS)
  passgen -p WORDS [-d SEPARATOR] [--wordlist PATH]
  passgen --passphrase -E BITS [-d SEPARATOR] [--wordlist PATH]

Password options:
  -a             Lowercase letters
  -A             Uppercase letters
  -0             Digits
  -!             Special characters
  -L N           Exact password length
  -E N           Target password entropy in bits

Passphrase options:
  -p N           Exact number of words
  --passphrase   Select passphrase mode (required with -E)
  -E N           Target passphrase entropy in bits
  -d STRING      Word separator (default: -)
  --wordlist PATH
                 Wordlist file (default: wordlist.csv beside this script)

General:
  -h, --help     Show help

Examples:
  passgen '-aA0!' -L 32
  passgen '-aA0!' -E 128
  passgen -p 6
  passgen -p 6 -d ' '
  passgen --passphrase -E 128
  passgen --passphrase -E 160 --wordlist ~/my-wordlist.csv""")


def valid_count(length, groups):
    """Count strings containing at least one character from every class."""
    alphabet_size = sum(len(group) for group in groups)
    total = 0

    for r in range(len(groups) + 1):
        for subset in itertools.combinations(groups, r):
            excluded = sum(len(group) for group in subset)
            total += (-1) ** r * (alphabet_size - excluded) ** length

    return total


def parse_args(args):
    selected = []
    length = None
    target_entropy = None
    word_count = None
    separator = "-"
    separator_set = False
    wordlist_path = DEFAULT_WORDLIST
    wordlist_set = False
    passphrase_requested = False
    i = 0

    while i < len(args):
        arg = args[i]

        if arg in ("-h", "--help"):
            usage()
            return None

        if arg == "--passphrase":
            passphrase_requested = True
            i += 1
            continue

        if arg in ("-L", "-E", "-p", "-d", "--wordlist"):
            if i + 1 >= len(args):
                raise ValueError(f"{arg} requires a value")

            value = args[i + 1]

            if arg in ("-L", "-E", "-p"):
                try:
                    number = int(value)
                except ValueError:
                    raise ValueError(f"Invalid integer for {arg}: {value!r}")

                if number < 1:
                    raise ValueError(f"{arg} must be positive")

                if arg == "-L":
                    if length is not None:
                        raise ValueError("Duplicate -L")
                    length = number
                elif arg == "-E":
                    if target_entropy is not None:
                        raise ValueError("Duplicate -E")
                    target_entropy = number
                else:
                    if word_count is not None:
                        raise ValueError("Duplicate -p")
                    word_count = number

            elif arg == "-d":
                if separator_set:
                    raise ValueError("Duplicate -d")
                separator = value
                separator_set = True

            else:
                if wordlist_set:
                    raise ValueError("Duplicate --wordlist")
                wordlist_path = Path(value).expanduser()
                wordlist_set = True

            i += 2
            continue

        if arg.startswith("-") and len(arg) > 1:
            for option in arg[1:]:
                if option not in CLASSES:
                    raise ValueError(f"Unknown option: -{option}")
                if option not in selected:
                    selected.append(option)
            i += 1
            continue

        raise ValueError(f"Unexpected argument: {arg!r}")

    passphrase_mode = (
        passphrase_requested
        or word_count is not None
        or separator_set
        or wordlist_set
    )

    if passphrase_mode:
        if selected or length is not None:
            raise ValueError(
                "Passphrase mode cannot be combined with character classes or -L"
            )

        if word_count is not None and target_entropy is not None:
            raise ValueError("Choose either -p or -E in passphrase mode")

        if word_count is None and target_entropy is None:
            raise ValueError(
                "Passphrase mode requires -p WORDS or --passphrase -E BITS"
            )

        if not separator:
            raise ValueError("Separator cannot be empty")

        if word_count is not None and word_count > MAX_LENGTH:
            raise ValueError(f"Word count cannot exceed {MAX_LENGTH}")

    else:
        if word_count is not None:
            raise ValueError("-p is only valid in passphrase mode")

        if (length is None) == (target_entropy is None):
            raise ValueError("Specify exactly one of -L or -E")

        if not selected:
            raise ValueError("Select at least one character class")

    return {
        "passphrase_mode": passphrase_mode,
        "selected": selected,
        "length": length,
        "target_entropy": target_entropy,
        "word_count": word_count,
        "separator": separator,
        "wordlist_path": wordlist_path,
    }


def generate_password(options):
    groups = [CLASSES[c] for c in options["selected"]]
    alphabet = "".join(groups)
    length = options["length"]
    target_entropy = options["target_entropy"]

    if length is None:
        for candidate in range(1, MAX_LENGTH + 1):
            count = valid_count(candidate, groups)
            if count > 0 and math.log2(count) >= target_entropy:
                length = candidate
                break
        else:
            raise ValueError("Target entropy exceeds supported length")

    if not 1 <= length <= MAX_LENGTH:
        raise ValueError(f"Length must be between 1 and {MAX_LENGTH}")

    if length < len(groups):
        raise ValueError("Length is too short for the selected classes")

    count = valid_count(length, groups)
    entropy = math.log2(count)

    # Rejection sampling gives a uniform distribution over valid passwords.
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if all(any(c in group for c in password) for group in groups):
            break

    print(password)
    print(
        f"Length: {length} characters | Entropy: {entropy:.2f} bits",
        file=sys.stderr,
    )


def load_wordlist(path):
    try:
        # utf-8-sig accepts UTF-8 files with or without a BOM.
        content = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"Cannot read wordlist {str(path)!r}: {exc}") from exc
    except UnicodeError as exc:
        raise ValueError(f"Wordlist is not valid UTF-8: {path}") from exc

    # Preserve punctuation and spelling; remove blank lines and duplicates.
    words = list(dict.fromkeys(
        line.strip() for line in content.splitlines() if line.strip()
    ))

    if len(words) < 2:
        raise ValueError("Wordlist must contain at least two distinct words")

    return words


def generate_passphrase(options):
    words = load_wordlist(options["wordlist_path"])
    word_count = options["word_count"]
    target_entropy = options["target_entropy"]
    word_entropy = math.log2(len(words))

    if word_count is None:
        word_count = math.ceil(target_entropy / word_entropy)

    if not 1 <= word_count <= MAX_LENGTH:
        raise ValueError(f"Word count must be between 1 and {MAX_LENGTH}")

    entropy = word_count * word_entropy
    passphrase = options["separator"].join(
        secrets.choice(words) for _ in range(word_count)
    )

    print(passphrase)
    print(
        f"Words: {word_count} | Wordlist: {len(words)} distinct words | "
        f"Entropy: {entropy:.2f} bits",
        file=sys.stderr,
    )


def main():
    options = parse_args(sys.argv[1:])

    if options is None:
        return 0

    if options["passphrase_mode"]:
        generate_passphrase(options)
    else:
        generate_password(options)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as exc:
        print(f"passgen: error: {exc}", file=sys.stderr)
        sys.exit(2)
