# passgen (v0.1)

**A cryptographically secure password and passphrase generator for the command line.**

`passgen` is a Python command-line utility for generating passwords and passphrases using Python's `secrets` module. It supports configurable password character classes, target entropy values, custom wordlists, configurable word separators, and optional random-character insertion into passphrases.

The repository also includes `wordlist_cleaner.py`, a companion utility for normalizing, filtering, deduplicating, and optionally consolidating similar wordlist entries.

The project aims to provide secure random generation, explicit entropy reporting, and practical tools for preparing wordlists.

## Features

- Cryptographically secure random choices using Python's `secrets` module.
- Password generation using lowercase letters, uppercase letters, digits, and special characters.
- All four password character classes enabled by default.
- Password generation by exact length or target entropy.
- Passphrase generation by exact word count or target generation-choice entropy.
- Optional insertion of one random character into a specified number of distinct passphrase word positions with `-R`.
- Custom wordlists and configurable passphrase separators.
- Duplicate and blank-line removal when loading a wordlist.
- Unicode normalization when loading passphrase wordlists and inserting characters.
- A wordlist cleaner that supports individual files or directories, including optional recursive discovery.
- Configurable input encoding and minimum word length in the cleaner.
- Optional filtering of orthographically similar words for memorability.
- Unit tests using Python's built-in `unittest` framework.

> **Development note:** Changes to the `-R` behavior and the planned `-C` and `-Cc` options are being considered. Until those changes are implemented, use the documented behavior of the current release.

## Requirements

- Python 3.
- The third-party Python package [`regex`](https://pypi.org/project/regex/), used for Unicode grapheme-cluster handling by `passgen.py`.
- A shell to use the optional Bash helper functions.

`wordlist_cleaner.py` uses the Python standard library. The generator requires `regex`.

## Installation

Clone or copy the repository to a directory of your choice. Create a virtual environment and install the dependency:

```bash
cd ~/scripts/shellutilities/passgen
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

The `requirements.txt` file contains the generator's external dependency.

Run the generator directly:

```bash
.venv/bin/python passgen.py --help
```

Run the cleaner's help:

```bash
.venv/bin/python wordlist_cleaner.py --help
```

The default passphrase wordlist is `wordlist.csv` in the same directory as `passgen.py`. Despite the filename extension, it is a newline-delimited text file, with one word per line; it is not parsed as a comma-separated CSV table.

### Optional Bash helpers

The repository includes shell helper functions for convenience. The `passgen.sh` helper currently uses the absolute path:

```text
$HOME/scripts/shellutilities/passgen/.venv/bin/python
$HOME/scripts/shellutilities/passgen/passgen.py
```

Adjust those paths if your checkout is in a different location. The test helpers are in `tests/test_passgen.sh` and `tests/test_wordlist_cleaner.sh`; they also expect the repository's virtual environment in the layout shown by the scripts.

## Password generation

### Default character classes

When no character classes are specified, all four classes are enabled:

| Option | Character class |
|---|---|
| `-a` | Lowercase ASCII letters (`a-z`) |
| `-A` | Uppercase ASCII letters (`A-Z`) |
| `-0` | Digits (`0-9`) |
| `-!` | Special characters: `!@#$%^&*()-_=+[]{}:,.?/` |

Every generated password must contain at least one character from each selected class.

Generate a 32-character password using the default classes:

```bash
.venv/bin/python passgen.py -L 32
```

Generate a password with a target entropy of at least 128 bits:

```bash
.venv/bin/python passgen.py -E 128
```

### Select character classes

Specify one or more classes to replace the default four-class policy. Class options can be combined:

```bash
# Lowercase letters and digits
.venv/bin/python passgen.py -a0 -L 24

# Uppercase and lowercase letters
.venv/bin/python passgen.py -aA -E 128

# Digits and special characters
.venv/bin/python passgen.py '-0!' -L 20
```

Quote arguments containing shell-special characters, especially `!`, `*`, `$`, and `&`, to prevent shell interpretation.

### Exact length: `-L`

`-L N` requests a password of exactly `N` characters. The supported maximum length is 4096 characters. The length must be sufficient to include at least one character from each selected class. For example, with all four default classes enabled, a password shorter than four characters cannot satisfy the class requirements.

```bash
.venv/bin/python passgen.py -L 32
```

### Target entropy: `-E`

`-E N` asks the generator to find the shortest supported password length whose valid password space reaches at least `N` bits of entropy.

```bash
.venv/bin/python passgen.py -E 128
```

The reported value may be higher than the requested target because password lengths are whole numbers.

Password mode requires exactly one of `-L` or `-E`.

## Passphrase generation

Passphrases are created by independently selecting words from the configured wordlist. Selection is with replacement, so the same word can occur more than once.

### Exact word count: `-p`

Use `-p N` to generate exactly `N` words:

```bash
.venv/bin/python passgen.py -p 6
```

The default separator is a hyphen. Set a different non-empty separator with `-d`:

```bash
# Separate words with spaces
.venv/bin/python passgen.py -p 6 -d ' '

# Separate words with underscores
.venv/bin/python passgen.py -p 6 -d '_'
```

Words in the loaded wordlist that contain the selected separator are rejected, so a separator cannot be confused with part of a word.

### Target generation-choice entropy

Use `--passphrase -E N` to choose the smallest supported word count whose estimated **generation-choice entropy** reaches the requested target:

```bash
.venv/bin/python passgen.py --passphrase -E 128
```

The `--passphrase` option is required when using `-E` to request passphrase entropy. Passphrase mode can instead use `-p N` to specify an exact word count, but `-p` and `-E` cannot be combined.

The maximum supported word count is 4096.

### Random-character insertion: `-R`

`-R N` inserts exactly one randomly selected character into each of `N` distinct word positions in the generated passphrase.

```bash
# Insert a character into one of six words
.venv/bin/python passgen.py -p 6 -R 1

# Insert characters into two distinct words
.venv/bin/python passgen.py -p 6 -R 2

# Insert one character into every word
.venv/bin/python passgen.py -p 6 -R 6

# Combine insertion with a target entropy
.venv/bin/python passgen.py --passphrase -E 128 -R 2
```

Current behavior and constraints:

- `-R` defaults to `0`, which means no characters are inserted.
- Each selected word position receives exactly one inserted character.
- The `N` positions are selected without replacement, so no position is selected more than once.
- The character and its insertion position are chosen using Python's `secrets` module.
- Characters that appear in the configured separator are excluded from the insertion alphabet.
- `-R` cannot exceed the number of words in the passphrase.
- The supported maximum for `-R` is 4096, subject to the word-count constraint.
- `-R` is a passphrase option and cannot be combined with password character classes or `-L`.

When used with `-p N`, the output contains exactly `N` words. When used with `--passphrase -E BITS`, the generator chooses a word count that reaches the target and accommodates the requested number of modified positions.

**Planned changes:** The behavior of `-R` may evolve, and the `-C` and `-Cc` options are planned features. They are not documented as available options in this release.

### Understanding passphrase entropy

For a wordlist with \(W\) distinct entries and a passphrase containing \(P\) independently selected words, the base generation-choice entropy is:

\[
H = P\log_2(W)
\]

With random-character insertion, the reported generation-choice entropy also accounts for the choice of distinct positions, inserted characters, and insertion positions. In the implementation, the estimate for `R > 0` is:

\[
H = P\log_2(W)
+\log_2\binom{P}{R}
+R\left(\log_2(A)+
\frac{1}{W}\sum_{i=1}^{W}\log_2(L_i+1)\right)
\]

where:

- \(W\) is the number of distinct words in the loaded wordlist.
- \(P\) is the number of words in the passphrase.
- \(R\) is the number of modified word positions.
- \(A\) is the size of the available insertion alphabet after separator characters are excluded.
- \(L_i\) is the number of grapheme clusters in word \(i\).

**Generation-choice entropy is not necessarily the exact entropy of the final output string.** Different internal random choices can produce the same output string, including because of Unicode normalization. The displayed value describes the generator's modeled random choices and should not be interpreted as a proof of the final string's exact Shannon entropy.

The `-E` option specifies a minimum target, not an exact value. The reported estimate may exceed it because the number of words is an integer.

## Custom wordlists

By default, `passgen.py` loads `wordlist.csv` from the directory containing the script. Supply another file with `--wordlist`:

```bash
.venv/bin/python passgen.py -p 6 --wordlist ~/my-wordlist.txt
```

Or combine a custom wordlist with a target entropy:

```bash
.venv/bin/python passgen.py --passphrase -E 160 \
  --wordlist ~/my-wordlist.txt
```

The file must be UTF-8 text, with one entry per line. UTF-8 files with or without a byte-order mark (BOM) are supported. Blank lines and duplicate entries are ignored when the wordlist is loaded. Entries are NFC-normalized, and at least two distinct words are required. A wordlist entry containing the selected separator is not allowed for a generated passphrase.

For dependable estimates, use a wordlist with known selection properties and enough distinct entries. The entropy estimate assumes uniform selection from the distinct loaded entries.

## Wordlist cleaner

`wordlist_cleaner.py` prepares wordlists for use with `passgen`. It accepts either an input file or a directory. It can extract entries from recognized Diceware-style records or treat a file as a simple one-entry-per-line list.

The cleaner does not intentionally modify source files. It writes a separate output file, normalizes and filters entries, removes duplicates, sorts the result alphabetically, and validates the written output.

### Basic usage

Clean a single file:

```bash
.venv/bin/python wordlist_cleaner.py ~/wordlists/source.txt
```

Clean files from a directory:

```bash
.venv/bin/python wordlist_cleaner.py ~/wordlists
```

For a directory input, the default output is written to the current working directory as `wordlist.unique.txt` (or `wordlist.memo.txt` when `--memo` is enabled). For a file input, the default output name is based on the input filename, such as `source.unique.txt` or `source.memo.txt`.

Specify the output explicitly with `-o` or `--output`:

```bash
.venv/bin/python wordlist_cleaner.py ~/wordlists/source.txt \
  --output ~/wordlists/cleaned.txt
```

The output directory is created if needed. The input and output paths must differ.

### Encoding

The default `--encoding auto` mode attempts to decode input using UTF-8 (including UTF-8 BOM handling), Windows-1252, and ISO-8859-1. Alternatively, specify an encoding:

```bash
.venv/bin/python wordlist_cleaner.py source.txt --encoding utf-8
.venv/bin/python wordlist_cleaner.py source.txt --encoding windows-1252
.venv/bin/python wordlist_cleaner.py source.txt --encoding iso-8859-1
```

Output is written as UTF-8 text.

### Minimum length and accepted entries

`--min-length N` sets the minimum word length. The default is four letters:

```bash
.venv/bin/python wordlist_cleaner.py source.txt --min-length 5
```

The cleaner normalizes entries using Unicode normalization and case folding, but its accepted output words are restricted to ASCII alphabetic characters. Entries containing non-ASCII letters, digits, punctuation, symbols, replacement characters, or fewer than the configured minimum number of letters are rejected. The output is normalized to lowercase and sorted alphabetically.

### Recursive directory processing

Use `-R` or `--recursive` to search a directory and its subdirectories:

```bash
.venv/bin/python wordlist_cleaner.py ~/wordlists --recursive
```

Without this option, directory processing is non-recursive.

### Similar-word filtering for memorability

Use `--memo` to remove orthographically similar words from the cleaned list:

```bash
.venv/bin/python wordlist_cleaner.py ~/wordlists --memo
```

`--memo-distance` controls the maximum edit distance used for filtering:

```bash
.venv/bin/python wordlist_cleaner.py ~/wordlists \
  --memo --memo-distance 1
```

Allowed distances are `1` and `2`; the default is `2`. Short words use a maximum edit distance of `1` when comparing words whose maximum length is five or fewer characters. The filtering is greedy and deterministic: candidates are considered in order of length and then alphabetically, and the final accepted list is sorted alphabetically. This option can substantially reduce the number of retained entries.

### Cleaner report and safety checks

The cleaner writes a report to standard error. Depending on the input and options, the report includes source files, line counts, blank lines, detected input formats, accepted and rejected entries, duplicates removed, similar words removed, and the destination path.

It reads source data before writing the final result, checks that at least two unique entries remain, writes UTF-8 output with LF line endings, and reads the output back to verify that its contents match the generated list and contain no duplicates.

## Output and entropy reporting

The generated password or passphrase is written to standard output. Generation metadata and cleaner reports are written to standard error, allowing the secret and diagnostic information to be redirected separately.

Example password metadata:

```text
Length: 32 characters | Entropy: 205.07 bits
```

Example passphrase metadata:

```text
Words: 6 | Characters: 52 (including separators), 46 (excluding separators) | Wordlist: 10000 distinct words | Generation-choice entropy: 90.00 bits
```

The values above are illustrative; actual values depend on the wordlist and options. Character counts describe the generated output, including any inserted characters. A fixed separator increases the output length but does not add entropy.

Password entropy is calculated from the number of valid strings satisfying the selected character-class requirements. Passphrase generation-choice entropy is calculated from the modeled random choices described above.

## Tests

The project uses Python's built-in `unittest` framework.

Run all discovered tests from the repository root:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Or run the test modules individually:

```bash
.venv/bin/python tests/test_passgen.py
.venv/bin/python tests/test_wordlist_cleaner.py
```

The current tests cover areas including:

- Password and passphrase argument validation.
- Passphrase generation-choice entropy calculations and word-count selection.
- Unicode normalization and entropy effects from insertion collisions.
- Character insertion at grapheme-cluster boundaries, including combining marks and emoji sequences.
- Wordlist loading, duplicate removal, separator validation, and minimum wordlist size.
- Wordlist filtering, minimum length, normalization, and rejection of unsupported entries.
- Levenshtein distance and the cleaner's similar-word filter, including comparisons against reference implementations.

The test suite validates functions and selected behavior with controlled inputs. It does not replace testing the complete CLI in the target environment.

## Security considerations

### Randomness

The generator uses Python's `secrets` module for secret-related random choices. It does not use the ordinary `random` module for password or passphrase generation.

### Password distribution

Password candidates are sampled and rejected unless every selected character class appears at least once. This rejection-sampling approach is intended to produce a uniform distribution over valid strings, assuming the underlying random choices are uniform.

### Wordlist quality and entropy

The passphrase entropy estimate assumes uniform, independent word selection from the distinct entries loaded by the program. It does not measure whether the source wordlist is predictable or whether its entries were chosen with bias. Cleaning a list does not make a weak or predictable source list secure.

### Random-character insertion

`-R` adds random choices to the generation process, but the entropy of those choices does not necessarily translate one-for-one into the entropy of the final output string. The output may contain collisions, including after Unicode normalization.

### Handling generated secrets

- Avoid placing real passwords directly in shell command arguments.
- Take care when redirecting secrets to files, logs, clipboard managers, or other applications.
- Terminal scrollback and shell pipelines can expose generated values.
- Do not commit generated credentials or other secrets to version control.
- Store generated passwords in a reputable password manager.

Entropy estimates do not protect against endpoint compromise, malware, clipboard exposure, insecure storage, or disclosure to the service where a credential is used.

## Command reference

### `passgen.py`

| Option | Description |
|---|---|
| `-a` | Include lowercase ASCII letters |
| `-A` | Include uppercase ASCII letters |
| `-0` | Include digits |
| `-!` | Include special characters |
| `-L N` | Generate a password of exactly `N` characters |
| `-E N` | Target password entropy in bits, or passphrase generation-choice entropy in passphrase mode |
| `-p N` | Generate a passphrase with exactly `N` words |
| `-R N` | Insert one random character into `N` distinct passphrase word positions; default: `0` |
| `--passphrase` | Explicitly select passphrase mode; required with passphrase `-E` |
| `-d STRING` | Set the passphrase separator; default: `-` |
| `--wordlist PATH` | Use a custom wordlist file |
| `-h`, `--help` | Show help |

Password mode requires exactly one of `-L` and `-E`. Passphrase mode requires either `-p` or `-E`; these options cannot be combined. Character-class options and `-L` cannot be combined with passphrase mode.

### `wordlist_cleaner.py`

| Option | Description |
|---|---|
| `INPUT` | Input wordlist file or directory |
| `-o PATH`, `--output PATH` | Output path |
| `--encoding MODE` | Input encoding: `auto`, `utf-8`, `iso-8859-1`, or `windows-1252`; default: `auto` |
| `--min-length N` | Minimum number of letters; default: `4` |
| `--memo` | Remove orthographically similar words for memorability |
| `--memo-distance N` | Maximum edit distance for `--memo`: `1` or `2`; default: `2` |
| `-R`, `--recursive` | Recursively search subdirectories |
| `-h`, `--help` | Show help |

## Limitations

- Maximum password length: 4096 characters.
- Maximum passphrase word count: 4096.
- `-R` cannot exceed the number of generated words.
- The passphrase wordlist must contain at least two distinct entries after loading.
- Wordlists are line-based; the generator does not parse CSV fields.
- The cleaner's accepted output entries are restricted to ASCII alphabetic words and the configured minimum length.
- The cleaner's `--memo` mode can significantly reduce the wordlist size.
- Entropy estimates depend on the generation model and the assumptions described above.
- Generation-choice entropy is not necessarily the exact entropy of the final passphrase string.

## License and wordlist provenance

No license is specified in this release's documentation.
You can find some wordlists in the link below.

<script src="https://gist.github.com/atoponce/95c4f36f2bc12ec13242a3ccc55023af.js"></script>
