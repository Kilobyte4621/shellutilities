
#!/usr/bin/env python3
"""Extract, normalize, and deduplicate wordlists."""

import argparse
import re
import sys
import unicodedata
from pathlib import Path


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

def levenshtein_distance(first, second):
    """Return the Levenshtein edit distance between two words."""
    if len(first) < len(second):
        first, second = second, first

    previous = list(range(len(second) + 1))

    for i, char_first in enumerate(first, start=1):
        current = [i]

        for j, char_second in enumerate(second, start=1):
            current.append(
                min(
                    current[j - 1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (
                        char_first != char_second
                    ),
                )
            )

        previous = current

    return previous[-1]


def filter_memorable_words(words, max_distance=2):
    """Keep the shortest word in each similarity component."""
    words = sorted(words)
    count = len(words)

    if count < 2:
        return words

    parent = list(range(count))
    rank = [0] * count

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first, second):
        root_first = find(first)
        root_second = find(second)

        if root_first == root_second:
            return

        if rank[root_first] < rank[root_second]:
            root_first, root_second = root_second, root_first

        parent[root_second] = root_first

        if rank[root_first] == rank[root_second]:
            rank[root_first] += 1

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

    # Index deletion signatures to find candidate pairs.
    signature_index = {}

    for index, word in enumerate(words):
        depth = min(1, max_distance) if len(word) <= 5 else max_distance
        signatures = deletion_signatures(word, depth)
        candidates = set()

        for signature in signatures:
            candidates.update(signature_index.get(signature, ()))

        for other_index in candidates:
            other_word = words[other_index]

            threshold = (
                1
                if max(len(word), len(other_word)) <= 5
                else max_distance
            )

            if abs(len(word) - len(other_word)) > threshold:
                continue

            if levenshtein_distance(word, other_word) <= threshold:
                union(index, other_index)

        for signature in signatures:
            signature_index.setdefault(signature, []).append(index)

        # Collect connected components.
    components = {}

    for index, word in enumerate(words):
        component = find(index)
        components.setdefault(component, []).append(word)

    # Keep the shortest word in each connected component.
    representatives = []
    group_details = []

    for members in components.values():
        representative = min(
            members,
            key=lambda word: (len(word), word),
        )
        representatives.append(representative)

        if len(members) > 1:
            group_details.append(
                (len(members), representative, sorted(members))
            )

    largest_groups = sorted(
        group_details,
        key=lambda group: (-group[0], group[1]),
    )[:10]

    print(
        f"Memo groups:        {len(components)}",
        file=sys.stderr,
    )
    print(
        f"Groups with 2+ words: {len(group_details)}",
        file=sys.stderr,
    )

    if largest_groups:
        print("Largest memo groups:", file=sys.stderr)

        for size, representative, members in largest_groups:
            examples = ", ".join(repr(word) for word in members[:12])

            if len(members) > 12:
                examples += ", ..."

            print(
                f"  {size} words; representative={representative!r}: "
                f"{examples}",
                file=sys.stderr,
            )

    return sorted(representatives)

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

    return entries, len(lines), detected_encoding, mode


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


def clean_wordlists(
    sources,
    destination,
    encoding="auto",
    min_length=3,
    keep_all=False,
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
        entries, line_count, detected_encoding, mode = read_wordlist(
            source, encoding
        )

        total_lines += line_count
        formats[mode] += 1
        blank_count += sum(
            not line.strip()
            for line in source.read_text(
                encoding=ENCODINGS[detected_encoding]
            ).splitlines()
        )

        for entry in entries:
            word = normalize_word(entry)

            if not word:
                continue

            if not keep_all and (
                not word.isalpha() or len(word) < min_length
            ):
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
        default=5,
        metavar="N",
        help="Minimum number of letters (default: 5)",
    )
    
    parser.add_argument(
        "--keep-all",
        action="store_true",
        help="Keep all extracted contents, including numbers and symbols",
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

    args = parser.parse_args()
    source = args.input.expanduser()

    if not source.exists():
        print(
            f"wordlist_cleaner: error: input does not exist: {source}",
            file=sys.stderr,
        )
        return 2

    if source.is_file():
        sources = [source]
        suffix = "memo" if args.memo else "unique"
        default_output = source.with_name(
            f"{source.stem}.{suffix}.txt"
        )
    elif source.is_dir():
        try:
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

        suffix = "memo" if args.memo else "unique"
        default_output = Path.cwd() / f"wordlist.{suffix}.txt"
    else:
        print(
            f"wordlist_cleaner: error: input is not a regular file "
            f"or directory: {source}",
            file=sys.stderr,
        )
        return 2

    destination = (
        args.output.expanduser()
        if args.output
        else default_output
    )

    try:
         clean_wordlists(
            sources,
            destination,
            encoding=args.encoding,
            min_length=args.min_length,
            keep_all=args.keep_all,
            memo=args.memo,
            memo_distance=args.memo_distance,
        )
    except (ValueError, OSError) as exc:
        print(f"wordlist_cleaner: error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
