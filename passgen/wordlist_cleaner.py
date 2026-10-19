
#!/usr/bin/env python3
"""Extract, normalize, and deduplicate wordlists."""

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from datetime import datetime


DICEWARE_RECORD = re.compile(
    r"^\s*(?:\d{4}|\d{5})[ \t]+(.+?)\s*$"
)

ENCODINGS = {
    "utf-8": "utf-8-sig",
    "iso-8859-1": "iso-8859-1",
    "windows-1252": "cp1252",
}


def positive_int(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "must be a positive integer"
        ) from exc

    if number < 1:
        raise argparse.ArgumentTypeError(
            "must be at least 1"
        )

    return number


def levenshtein_distance(first, second, max_distance=None):
    """Return Levenshtein distance, optionally bounded by max_distance."""
    if first == second:
        return 0

    if len(first) < len(second):
        first, second = second, first

    len_first = len(first)
    len_second = len(second)

    if max_distance is not None:
        if max_distance < 0:
            raise ValueError("max_distance must be non-negative")

        if len_first - len_second > max_distance:
            return max_distance + 1

        if not second:
            return len_first if len_first <= max_distance else max_distance + 1

        # Compute only the diagonal band that can stay within the limit.
        previous = list(range(len_second + 1))
        infinity = max_distance + 1

        for i, char_first in enumerate(first, start=1):
            start = max(1, i - max_distance)
            end = min(len_second, i + max_distance)

            current = [infinity] * (len_second + 1)
            if start == 1:
                current[0] = i

            row_min = infinity

            for j in range(start, end + 1):
                current[j] = min(
                    current[j - 1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (char_first != second[j - 1]),
                )
                row_min = min(row_min, current[j])

            if row_min > max_distance:
                return infinity

            previous = current

        distance = previous[len_second]
        return distance if distance <= max_distance else infinity

    previous = list(range(len_second + 1))

    for i, char_first in enumerate(first, start=1):
        current = [i]

        for j, char_second in enumerate(second, start=1):
            current.append(
                min(
                    current[j - 1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (char_first != char_second),
                )
            )

        previous = current

    return previous[-1]



def filter_memorable_words(words, max_distance=2):
    """Greedily keep words that are not too similar to accepted words."""
    ordered_words = sorted(
        set(words),
        key=lambda word: (len(word), word),
    )

    if len(ordered_words) < 2:
        return ordered_words

    accepted = []

    def deletion_signatures(word, depth):
        signatures = {word}
        frontier = {word}

        for _ in range(depth):
            frontier = {
                variant[:position] + variant[position + 1:]
                for variant in frontier
                for position in range(len(variant))
            }
            signatures.update(frontier)

        return signatures

    # Index signatures of accepted words only.
    signature_index = {}

    for word in ordered_words:
        signatures = deletion_signatures(word, max_distance)
        candidates = set()

        for signature in signatures:
            candidates.update(signature_index.get(signature, ()))

        is_similar = False

        for other_index in candidates:
            other_word = accepted[other_index]

            threshold = (
                1
                if max(len(word), len(other_word)) <= 5
                else max_distance
            )

            if abs(len(word) - len(other_word)) > threshold:
                continue

            if levenshtein_distance(
                word,
                other_word,
                max_distance=threshold,
            ) <= threshold:
                is_similar = True
                break

        if is_similar:
            continue

        word_index = len(accepted)
        accepted.append(word)

        for signature in signatures:
            signature_index.setdefault(signature, []).append(word_index)

    # The cleaner's output remains alphabetically sorted.
    return sorted(accepted)



def decode_content(data, requested_encoding):
    if requested_encoding != "auto":
        try:
            return (
                data.decode(ENCODINGS[requested_encoding]),
                requested_encoding,
            )
        except UnicodeError as exc:
            raise ValueError(
                f"Input is not valid {requested_encoding}: {exc}"
            ) from exc

    for codec, label in (
        ("utf-8-sig", "utf-8"),
        ("cp1252", "windows-1252"),
        ("iso-8859-1", "iso-8859-1"),
    ):
        try:
            return data.decode(codec), label
        except UnicodeError:
            continue

    raise ValueError("Unable to decode input file")


def normalize_word(line):
    word = unicodedata.normalize("NFC", line.strip())
    return unicodedata.normalize("NFC", word.casefold())


def extract_entries(lines):
    records = [
        match
        for line in lines
        if (match := DICEWARE_RECORD.fullmatch(line))
    ]

    if records:
        return [match.group(1) for match in records], "diceware"

    return [line for line in lines if line.strip()], "simple"


def read_wordlist(source, encoding):
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise ValueError(
            f"Cannot read {str(source)!r}: {exc}"
        ) from exc

    content, detected_encoding = decode_content(data, encoding)
    lines = content.splitlines()
    entries, mode = extract_entries(lines)
    blank_count = sum(not line.strip() for line in lines)

    return (
        entries,
        len(lines),
        detected_encoding,
        mode,
        blank_count,
    )


def write_output(destination, words):
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            "\n".join(words) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        written = destination.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(
            f"Cannot write or verify {str(destination)!r}: {exc}"
        ) from exc

    output_words = written.splitlines()

    if (
        output_words != words
        or len(set(output_words)) != len(output_words)
    ):
        raise ValueError("Output verification failed")

def get_available_output(destination):
    """Return a non-existing output path without overwriting files."""
    if not destination.exists():
        return destination

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = destination.with_name(
        f"{destination.stem}.{timestamp}{destination.suffix}"
    )

    counter = 1

    while candidate.exists():
        candidate = destination.with_name(
            f"{destination.stem}.{timestamp}.{counter}{destination.suffix}"
        )
        counter += 1

    return candidate

def clean_wordlists(
    sources,
    destination,
    encoding="auto",
    min_length=4,
    memo=False,
    memo_distance=2,
):
    destination_resolved = destination.resolve()
    sources = [
        source for source in sources
        if source.resolve() != destination_resolved
    ]

    if not sources:
        raise ValueError("No input files to process")

    seen = set()
    unique_words = []
    total_lines = 0
    blank_count = 0
    accepted_count = 0
    rejected_count = 0
    duplicate_count = 0
    formats = {"diceware": 0, "simple": 0}

    # Process all inputs before writing the final output.
    for source in sources:

        entries, line_count, detected_encoding, mode, file_blank_count = (
            read_wordlist(source, encoding)
        )

        total_lines += line_count
        formats[mode] += 1

        blank_count += file_blank_count

        for entry in entries:
            word = normalize_word(entry)

            if not word:
                continue

            if "\uFFFD" in word:
                rejected_count += 1
                continue

            if not word.isascii() or not word.isalpha():
                rejected_count += 1
                continue


            if len(word) < min_length:
                rejected_count += 1
                continue

            accepted_count += 1

            if word in seen:
                duplicate_count += 1
                continue

            seen.add(word)
            unique_words.append(word)

        
    memo_removed_count = 0

    if memo:
        original_count = len(unique_words)
        unique_words = filter_memorable_words(
            unique_words,
            max_distance=memo_distance,
        )
        memo_removed_count = original_count - len(unique_words)

    if len(unique_words) < 2:
        raise ValueError(
            "The consolidated wordlist must contain at least "
            "two distinct entries"
        )

    unique_words.sort()
    write_output(destination, unique_words)

    print(f"Input files:        {len(sources)}", file=sys.stderr)
    print(f"Input lines:        {total_lines}", file=sys.stderr)
    print(f"Blank lines:        {blank_count}", file=sys.stderr)
    print(f"Diceware files:     {formats['diceware']}", file=sys.stderr)
    print(f"Simple files:       {formats['simple']}", file=sys.stderr)
    print(f"Accepted entries:   {accepted_count}", file=sys.stderr)
    print(f"Rejected entries:   {rejected_count}", file=sys.stderr)
    print(f"Duplicates removed:{duplicate_count:>6}", file=sys.stderr)
    if memo:
        print(
            f"Memo words removed: {memo_removed_count}",
            file=sys.stderr,
        )
    print(f"Unique entries:     {len(unique_words)}", file=sys.stderr)
    print(f"Output file:        {destination}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Normalize and consolidate wordlists from a file "
            "or directory. Original inputs are not modified."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input wordlist file or directory",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output path",
    )
    parser.add_argument(
        "--encoding",
        choices=("auto", "utf-8", "iso-8859-1", "windows-1252"),
        default="auto",
        help="Input encoding (default: auto)",
    )
    parser.add_argument(
        "--min-length",
        type=positive_int,
        default=4,
        metavar="N",
        help="Minimum number of letters (default: 4)",
    )
    parser.add_argument(
        "--memo",
        action="store_true",
        help="Remove orthographically similar words for memorization",
    )
    parser.add_argument(
        "--memo-distance",
        type=int,
        choices=(1, 2),
        default=2,
        metavar="N",
        help=(
            "Maximum edit distance for --memo: 1 or 2 "
            "(default: 2; short words use a maximum of 1)"
        ),
    )
    parser.add_argument(
        "-R", "--recursive",
        action="store_true",
        help="Recursively search for wordlist files in subdirectories",
    )    

    args = parser.parse_args()
    source = args.input.expanduser()

    if not source.exists():
        print(
            f"wordlist_cleaner: error: input does not exist: {source}",
            file=sys.stderr,
        )
        return 2

    suffix = "memo" if args.memo else "unique"

    if source.is_file():
        sources = [source]
        output_name = f"{source.stem}.{suffix}.txt"

    elif source.is_dir():
        try:
            if args.recursive:
                sources = sorted(
                    path for path in source.rglob("*")
                    if path.is_file()
                )
            else:
                sources = sorted(
                    path for path in source.iterdir()
                    if path.is_file()
                )
        except OSError as exc:
            print(
                f"wordlist_cleaner: error: cannot list directory: {exc}",
                file=sys.stderr,
            )
            return 2

        output_name = f"{source.name}.{suffix}.txt"

    else:
        print(
            f"wordlist_cleaner: error: input is not a regular file "
            f"or directory: {source}",
            file=sys.stderr,
        )
        return 2

    default_output = Path.cwd() / "wordlists" / output_name

    destination = (
        args.output.expanduser()
        if args.output
        else default_output
    )

    if not args.output:
        destination = get_available_output(destination)

    try:
         clean_wordlists(
            sources,
            destination,
            encoding=args.encoding,
            min_length=args.min_length,
            memo=args.memo,
            memo_distance=args.memo_distance,
        )
    except (ValueError, OSError) as exc:
        print(f"wordlist_cleaner: error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
