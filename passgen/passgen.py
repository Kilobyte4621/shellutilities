#!/usr/bin/env python3

# Cryptographically secure password generator.

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

def usage():
    print("""Usage: passgen (-L LENGTH | -E BITS) -aA0!
Options:
  -a  Include lowercase letters
  -A  Include uppercase letters
  -0  Include digits
  -!  Include special characters
  -L N  Exact password length
  -E N  Minimum entropy in bits
  -h    Show this help

Examples:
  passgen -aA0! -L 32
  passgen -a0 -E 100
  passgen -aA0! -E 128""")

args = sys.argv[1:]
selected = []
length = None
entropy = None
i = 0

while i < len(args):
    arg = args[i]

    if arg in ("-h", "--help"):
        usage()
        sys.exit(0)

    if arg in ("-L", "-E"):
        if i + 1 >= len(args):
            sys.exit(f"Error: {arg} requires a value.")
        try:
            value = int(args[i + 1])
        except ValueError:
            sys.exit(f"Error: invalid value for {arg}.")
        if value < 1:
            sys.exit("Error: length and entropy must be positive.")
        if arg == "-L":
            if length is not None:
                sys.exit("Error: duplicate -L.")
            length = value
        else:
            if entropy is not None:
                sys.exit("Error: duplicate -E.")
            entropy = value
        i += 2
        continue

    if arg.startswith("-") and len(arg) > 1:
        for option in arg[1:]:
            if option not in CLASSES:
                sys.exit(f"Error: unknown option -{option}.")
            if option not in selected:
                selected.append(option)
        i += 1
        continue

    sys.exit(f"Error: unexpected argument {arg!r}.")

if (length is None) == (entropy is None):
    sys.exit("Error: specify exactly one of -L or -E.")

if not selected:
    sys.exit("Error: select at least one character class.")

alphabets = [CLASSES[c] for c in selected]
alphabet = "".join(alphabets)
pool_size = len(alphabet)

if length is None:
    # Conservative lower bound on the entropy of valid outputs.
    class_entropy = sum(math.log2(len(s)) for s in alphabets)
    length = max(
        len(selected),
        math.ceil(
            len(selected)
            + (entropy - class_entropy) / math.log2(pool_size)
        ),
    )

if length < len(selected):
    sys.exit("Error: length is too short for the selected classes.")

# Rejection sampling gives a uniform distribution over valid strings.
while True:
    password = "".join(
        secrets.choice(alphabet) for _ in range(length)
    )
    if all(any(c in group for c in password) for group in alphabets):
        break

print(password)

