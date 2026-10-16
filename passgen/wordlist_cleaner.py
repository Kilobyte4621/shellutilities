#!/usr/bin/env python3
"""Normalize and deduplicate a newline-delimited wordlist."""

import argparse
import sys
import unicodedata
from pathlib import Path


def normalize_word(line):
    """Normalize whitespace, Unicode representation, and letter case."""
    word = unicodedata.normalize("NFC", line.strip())
    word = word.casefold()
    return unicodedata.normalize("NFC", word)


def clean_wordlist(source, destination):
    try:
        content = source.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"Cannot read input file {str(source)!r}: {exc}") from exc
    except UnicodeError as exc:
        raise ValueError(f"Input file is not valid UTF-8: {source}") from exc

    lines = content.splitlines()
    unique_words = []
    seen = set()
    blank_count = 0
    duplicate_count = 0

    for line in lines:
        if not line.strip():
            blank_count += 1
            continue

        word = normalize_word(line)

        if not word:
            blank_count += 1
            continue

        if word in seen:
            duplicate_count += 1
            continue

        seen.add(word)
        unique_words.append(word)

    if len(unique_words) < 2:
        raise ValueError(
            "The cleaned wordlist must contain at least two distinct entries"
        )

    if source.resolve() == destination.resolve():
        raise ValueError("Input and output paths must be different")

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            "\n".join(unique_words) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        raise ValueError(
            f"Cannot write output file {str(destination)!r}: {exc}"
        ) from exc

    # Read back the output to verify its contents and uniqueness.
    try:
        written = destination.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(
            f"Cannot verify output file {str(destination)!r}: {exc}"
        ) from exc

    output_words = written.splitlines()

    if output_words != unique_words or len(set(output_words)) != len(output_words):
        raise ValueError("Output verification failed")

    print(f"Input lines:       {len(lines)}", file=sys.stderr)
    print(f"Blank lines:       {blank_count}", file=sys.stderr)
    print(f"Duplicates removed:{duplicate_count:>6}", file=sys.stderr)
    print(f"Unique entries:    {len(unique_words)}", file=sys.stderr)
    print(f"Output file:       {destination}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Normalize and deduplicate a newline-delimited UTF-8 wordlist. "
            "The original file is not modified."
        )
    )
    parser.add_argument("input", type=Path, help="Original wordlist file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path (default: INPUT.unique.txt)",
    )
    args = parser.parse_args()

    source = args.input.expanduser()
    destination = (
        args.output.expanduser()
        if args.output
        else source.with_name(f"{source.stem}.unique.txt")
    )

    try:
        clean_wordlist(source, destination)
    except ValueError as exc:
        print(f"wordlist_cleaner: error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
