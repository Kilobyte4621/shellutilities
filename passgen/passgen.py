
#!/usr/bin/env python3
"""Cryptographically secure password generator."""

import itertools
import math
import secrets
import string
import sys

CLASSES = {
    "a": string.ascii_lowercase,
    "A": string.ascii_uppercase,
    "0": string.digits,
    "!": "!@#$%^&*()-_=+[]{}:,.?/",
}

MAX_LENGTH = 4096


def usage():
    print("""Usage: passgen (-L LENGTH | -E BITS) -aA0!
Options:
  -a  Lowercase letters
  -A  Uppercase letters
  -0  Digits
  -!  Special characters
  -L N  Exact password length
  -E N  Target entropy in bits
  -h    Show help

Examples:
  passgen '-aA0!' -L 32
  passgen '-aA0!' -E 128
  passgen '-a0' -E 100""")


def valid_count(length, groups):
    """Count strings containing at least one character from every class."""
    alphabet_size = sum(len(group) for group in groups)
    total = 0

    for r in range(len(groups) + 1):
        for subset in itertools.combinations(groups, r):
            excluded = sum(len(group) for group in subset)
            count = (alphabet_size - excluded) ** length
            total += (-1) ** r * count

    return total


def main():
    args = sys.argv[1:]
    selected = []
    length = None
    target_entropy = None
    i = 0

    while i < len(args):
        arg = args[i]

        if arg in ("-h", "--help"):
            usage()
            return 0

        if arg in ("-L", "-E"):
            if i + 1 >= len(args):
                raise ValueError(f"{arg} requires a value")

            try:
                value = int(args[i + 1])
            except ValueError:
                raise ValueError(f"Invalid value for {arg}")

            if value < 1:
                raise ValueError(f"{arg} must be positive")

            if arg == "-L":
                if length is not None:
                    raise ValueError("Duplicate -L")
                length = value
            else:
                if target_entropy is not None:
                    raise ValueError("Duplicate -E")
                target_entropy = value

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

    if (length is None) == (target_entropy is None):
        raise ValueError("Specify exactly one of -L or -E")

    if not selected:
        raise ValueError("Select at least one character class")

    groups = [CLASSES[c] for c in selected]
    alphabet = "".join(groups)

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

    # Rejection sampling produces a uniform valid password.
    while True:
        password = "".join(
            secrets.choice(alphabet) for _ in range(length)
        )
        if all(any(c in group for c in password) for group in groups):
            break

    print(password)
    print(
        f"Length: {length} characters | "
        f"Entropy: {entropy:.2f} bits",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as exc:
        print(f"passgen: error: {exc}", file=sys.stderr)
        sys.exit(2)
