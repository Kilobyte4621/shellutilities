# passgen (v0.0.6)

**A cryptographically secure password and passphrase generator for the command line.**

`passgen` is a lightweight Python utility for generating random passwords and passphrases using Python's `secrets` module. It supports configurable character classes, minimum entropy targets, custom wordlists, selectable word separators, and optional random-character insertion into passphrases.

The project also includes `wordlist_cleaner.py`, a companion utility for normalizing and deduplicating wordlists before using them to generate passphrases.

The goal is to provide secure defaults for everyday use while keeping customization, entropy estimation, testing, and wordlist maintenance straightforward.

## Features

- Cryptographically secure random selection using Python's `secrets` module.
- Four character classes for passwords: lowercase letters, uppercase letters, digits, and special characters.
- All four character classes enabled by default for password generation.
- Optional character-class selection for custom password policies.
- Password generation by exact length or minimum entropy target.
- Passphrase generation by exact word count or minimum entropy target.
- Optional insertion of one random character into a specified number of distinct passphrase words.
- Random selection of modified word positions, insertion characters, and insertion positions.
- Entropy estimation that accounts for password character-class constraints.
- Generation-choice entropy estimation for passphrases using random-character insertion.
- Custom wordlists and configurable passphrase separators.
- UTF-8 wordlists supported, including files with a UTF-8 BOM.
- Automatic removal of duplicate word entries during passphrase generation.
- Wordlist preprocessing with `wordlist_cleaner.py`.
- Unicode normalization and case-insensitive deduplication in the cleaner.
- Cleaning reports with counts of blank lines, removed duplicates, and unique entries.
- Original wordlists are preserved by default.
- Passwords and passphrases written to standard output; metadata written to standard error.
- Unit tests using Python's built-in `unittest` framework.
- No third-party Python dependencies.

## Requirements

- Python 3.8 or newer.
- A Unix-like environment with a shell for the provided wrapper.

The Python scripts can also be invoked directly on systems where Python 3 is available.

## Installation

Place the project files in your preferred scripts directory. For example:

```text
passgen/
├── passgen.py
├── passgen.sh
├── wordlist_cleaner.py
├── wordlist.csv
└── tests/
    └── test_passgen.py
```

The default `wordlist.csv` is a newline-delimited wordlist, not a conventional comma-separated CSV table.

Make the Python scripts executable:

```bash
chmod +x ~/scripts/shellutilities/passgen/passgen.py
chmod +x ~/scripts/shellutilities/passgen/wordlist_cleaner.py
```

The provided shell wrapper defines a `passgen` function that invokes the password generator. If your shell automatically loads functions from `~/scripts`, ensure the wrapper is loaded by your shell configuration.

Alternatively, invoke the generator directly:

```bash
python3 ~/scripts/shellutilities/passgen/passgen.py -L 32
```

Check the available generator options:

```bash
passgen --help
```

Check the wordlist cleaner options:

```bash
python3 ~/scripts/shellutilities/passgen/wordlist_cleaner.py --help
```

## Password generation

### Default behavior

When no character classes are specified, `passgen` uses all four classes:

- Lowercase letters: `a-z`
- Uppercase letters: `A-Z`
- Digits: `0-9`
- Special characters: `!@#$%^&*()-_=+[]{}:,.?/`

Generate a 32-character password:

```bash
passgen -L 32
```

Generate a password with at least 128 bits of entropy:

```bash
passgen -E 128
```

Every generated password must contain at least one character from each selected class.

### Character classes

Character classes can be combined in a single argument or specified separately.

| Option | Character class |
|---|---|
| `-a` | Lowercase letters |
| `-A` | Uppercase letters |
| `-0` | Digits |
| `-!` | Special characters |

When specifying classes, only the selected classes are used. The default four-class policy is replaced by the explicitly selected classes.

For example, generate a password containing only lowercase letters and digits:

```bash
passgen -a0 -L 24
```

Generate a password using uppercase and lowercase letters:

```bash
passgen -aA -E 128
```

Generate a password using digits and special characters:

```bash
passgen '-0!' -L 20
```

**Note:** Quote arguments containing special characters when invoking the command from a shell. This prevents shell expansion and interpretation of characters such as `!`, `*`, `$`, and `&`.

### Exact length

Use `-L` to specify the exact number of characters:

```bash
passgen -L 32
```

The length must be between 1 and 4096. The password must also be long enough to include at least one character from every selected class. For example, the default four-class configuration cannot generate a valid password shorter than four characters.

### Entropy target

Use `-E` to specify the minimum desired password entropy in bits:

```bash
passgen -E 128
```

The generator determines the shortest supported length whose number of valid passwords meets the requested entropy target.

The reported entropy can exceed the requested value because password length is an integer.

## Passphrase generation

Passphrases are generated by independently selecting words from a wordlist using `secrets.choice()`.

Word selection is performed with replacement, so the same word may appear more than once in a passphrase.

### Exact word count

Use `-p` to specify the number of words:

```bash
passgen -p 6
```

By default, words are joined with a hyphen. To use spaces instead:

```bash
passgen -p 6 -d ' '
```

A custom separator can be any non-empty string:

```bash
passgen -p 5 -d '_'
```

The output metadata includes the number of words, total character count including and excluding separators, wordlist size, and estimated entropy.

### Entropy target

Use `--passphrase -E` to request a minimum passphrase entropy:

```bash
passgen --passphrase -E 128
```

The generator calculates the smallest supported word count whose **generation-choice entropy** meets the requested target, rounding up to a whole number of words. This estimates the entropy of the generator's internal random choices, not necessarily the exact entropy of the final passphrase string. With random-character insertion (`-R` greater than zero), different random choices can produce identical output strings, particularly when Unicode normalization causes collisions.

For example, if the wordlist contains 46,201 distinct words, each independently selected word contributes approximately 15.50 bits of entropy. A 128-bit target therefore requires nine words, providing approximately 139.46 bits without random-character insertion.

The number of words is limited to 4096.

### Random-character insertion (`-R`)

The `-R N` option inserts exactly one cryptographically random character into each of `N` distinct words in the generated passphrase.

The character is inserted at a randomly selected position within the word. Existing characters are preserved; no original character is replaced or removed.

#### Usage

Insert a random character into one of six words:

```bash
passgen -p 6 -R 1
```

Insert random characters into two distinct words:

```bash
passgen -p 6 -R 2
```

Insert one random character into every word:

```bash
passgen -p 6 -R 6
```

Combine insertion with an entropy target:

```bash
passgen --passphrase -E 128 -R 2
```

Use a custom separator:

```bash
passgen -p 6 -R 2 -d '_'
```

#### Behavior and constraints

- `-R` defaults to `0`, which means no characters are inserted.
- Each modified word receives exactly one inserted character.
- The generator selects `N` distinct word positions randomly, without replacement. A word position cannot be selected more than once.
- The inserted character and its position within the word are selected using Python's `secrets` module.
- Characters present in the configured separator are excluded from the insertion alphabet. This prevents an inserted character from being confused with a word separator.
- `-R` cannot exceed the generated word count.
- The supported value of `-R` is between 0 and 4096, subject to the word-count constraint.
- `-R` is a passphrase option and cannot be combined with password character classes or `-L`.

When using `-p N`, the word count is exactly `N`.

When using `--passphrase -E BITS`, the generator calculates the smallest supported word count that meets the target for the selected `-R` value. The chosen word count is at least as large as `N` in `-R N`, because each modified position must correspond to a generated word.

#### Entropy reporting with `-R`

The program reports `Generation-choice entropy` for both `-R 0` and `-R` greater than zero.
- Without insertion, this value equals the final output entropy under the documented model, assuming distinct normalized wordlist entries and an unambiguous fixed separator.
- With insertion, different internal random choices can produce identical output strings, so generation-choice entropy may exceed final output entropy. The calculation accounts for:

1. Independent word selections from the wordlist.
2. Selection of distinct word positions to modify.
3. Random inserted-character choices.
4. Random insertion positions within the selected words.

Let:

- \(W\) be the number of distinct words in the wordlist.
- \(P\) be the number of generated words.
- \(R\) be the number of modified word positions.
- \(A\) be the size of the available insertion alphabet.
- \(L_i\) be the length of word \(i\) in the wordlist.

For `R = 0`, the estimated entropy is:

\[
H = P\log_2(W)
\]

For `R > 0`, the generation-choice entropy is calculated as:

\[
H = P\log_2(W)
+\log_2\binom{P}{R}
+R\left(\log_2(A)+
\frac{1}{W}\sum_{i=1}^{W}\log_2(L_i+1)\right)
\]

The insertion-position term uses the average over the wordlist because the specific words are selected randomly.

**Important:** Generation-choice entropy describes the entropy of the generator's internal random choices. It is not necessarily the exact entropy of the final output string, because different internal choices can theoretically produce identical strings.

The `-E` option specifies a minimum target, not an exact value. The reported estimate may exceed the requested target.

### Custom wordlists

By default, `passgen` reads `wordlist.csv` from the same directory as `passgen.py`.

Specify another wordlist with `--wordlist`:

```bash
passgen -p 6 --wordlist ~/my-wordlist.txt
```

Or combine a custom wordlist with an entropy target:

```bash
passgen --passphrase -E 160 --wordlist ~/my-wordlist.txt
```

The wordlist format is **one word or entry per line**, not a comma-separated CSV table, despite the default filename extension.

Wordlists must be valid UTF-8 text and contain at least two distinct non-empty entries. UTF-8 files with or without a byte-order mark (BOM) are supported. Blank lines and duplicate entries are ignored during passphrase generation, and punctuation within entries is preserved.

For reliable entropy estimates, use a wordlist with sufficient size and entries appropriate for your intended use. Avoid wordlists with predictable or heavily biased content.

## Wordlist cleaner

`wordlist_cleaner.py` is a standalone utility for preparing a wordlist before using it with `passgen`.

It reads a newline-delimited UTF-8 text file, normalizes each entry, removes duplicates, and writes a cleaned wordlist. The original file is not modified.

### What it does

The cleaner applies the following operations in order:

1. Reads UTF-8 text, accepting files with or without a UTF-8 BOM.
2. Removes leading and trailing whitespace from each line.
3. Discards blank lines.
4. Normalizes Unicode text to NFC.
5. Converts entries to lowercase using Python's Unicode-aware `casefold()`.
6. Normalizes the result to NFC again.
7. Removes duplicate entries while preserving the order of their first normalized occurrence.
8. Writes the resulting entries as UTF-8 without a BOM, using one entry per line.
9. Reads the output back and verifies that the contents match the generated entries and contain no duplicates.

Internal punctuation and accents are preserved. The cleaner does not remove hyphens, apostrophes, or other punctuation automatically.

Because `casefold()` performs more comprehensive case normalization than `lower()`, some Unicode strings that differ in spelling or representation may be treated as equivalent. For example, `Straße` and `STRASSE` normalize to the same entry, `strasse`.

Unicode NFC normalization unifies canonically equivalent representations of characters without removing accents. Therefore, `café` and `cafe` remain distinct entries.

### Basic usage

Run the cleaner on the default wordlist:

```bash
python3 ~/scripts/shellutilities/passgen/wordlist_cleaner.py \
  ~/scripts/shellutilities/passgen/wordlist.csv
```

By default, the output filename is derived from the input filename. For example:

```text
wordlist.csv -> wordlist.unique.txt
```

The source file remains unchanged.

### Specify an output path

Use `-o` or `--output` to choose the destination:

```bash
python3 ~/scripts/shellutilities/passgen/wordlist_cleaner.py \
  ~/scripts/shellutilities/passgen/wordlist.csv \
  --output ~/wordlists/wordlist.unique.txt
```

The output directory is created if necessary.

The input and output paths must be different. The cleaner rejects a result containing fewer than two unique non-empty entries.

### Example

Suppose the source wordlist contains:

```text
 Apple
apple
CAFÉ
café
cafe
Straße
STRASSE
mother-in-law

```

The cleaned output will be:

```text
apple
café
cafe
strasse
mother-in-law
```

The first normalized occurrence of each unique entry is retained. Duplicate entries and blank lines are discarded.

### Cleaner report

The cleaner writes a summary to standard error, including:

- Total input lines.
- Blank lines discarded.
- Duplicate entries removed.
- Unique entries written.
- Output file path.

For example:

```text
Input lines:          8
Blank lines:          1
Duplicates removed:  2
Unique entries:       5
Output file:          wordlist.unique.txt
```

The numbers depend on the input file.

### Use the cleaned wordlist with passgen

Once the cleaned wordlist has been generated, pass it to the generator explicitly:

```bash
passgen --passphrase -E 128 \
  --wordlist ~/scripts/shellutilities/passgen/wordlist.unique.txt
```

Or generate a fixed number of words:

```bash
passgen -p 6 \
  --wordlist ~/scripts/shellutilities/passgen/wordlist.unique.txt
```

Cleaning the wordlist beforehand makes its contents easier to inspect and ensures that case variants and canonically equivalent Unicode entries do not inflate the reported wordlist size.

**Important:** Cleaning is a preprocessing step, not a substitute for choosing a suitable wordlist. The estimated passphrase entropy depends on the number of distinct entries remaining after normalization and on the generator's uniform selection process.

## Understanding entropy

Entropy estimates describe the size of the generator's possible output space, assuming uniformly random selection and the generation rules implemented by the script.

### Password entropy

For a password of length \(L\), let \(N\) be the number of valid passwords that satisfy the selected character-class requirements.

The reported entropy is:

\[
H = \log_2(N)
\]

The calculation accounts for the requirement that every selected character class appears at least once.

Consequently, entropy is not necessarily equal to length multiplied by the logarithm of the combined alphabet size: the mandatory class requirements reduce the set of valid outputs.

### Passphrase entropy without insertion

For a wordlist containing \(W\) distinct entries and a passphrase containing \(P\) independently selected words, the estimated entropy is:

\[
H = P\log_2(W)
\]

This calculation assumes each distinct entry has an equal probability of selection, words are selected independently, and repetition is allowed.

The separator does not contribute entropy because it is fixed by the user.

### Interpreting the output

The generated password or passphrase is printed to standard output. Metadata is printed to standard error.

Password example:

```text
Length: 32 characters | Entropy: 205.07 bits
```

Passphrase example without insertion:

```text
Words: 9 | Characters: 76 (including separators), 68 (excluding separators) | Wordlist: 46201 distinct words | Entropy: 139.46 bits
```

Passphrase example with insertion:

```text
Words: 7 | Characters: 52 (including separators), 46 (excluding separators) | Wordlist: 46201 distinct words | Generation-choice entropy: 131.31 bits
```

The exact values depend on the wordlist, separator, and selected options.

The character count is the length of the actual generated passphrase. The count including separators reflects the final output string; the count excluding separators is the combined length of the generated words after any insertions.

A fixed separator increases the total number of characters but does not increase entropy.

Separating the secret from the metadata allows the generated value to be captured independently.

## Tests

The project includes unit tests in `tests/test_passgen.py`, implemented with Python's built-in `unittest` framework.

### Run the tests

From the `passgen` project directory:

```bash
python3 -m unittest discover -s tests -v
```

The tests can also be run directly by specifying the test module:

```bash
python3 -m unittest discover \
  -s ~/scripts/shellutilities/passgen/tests \
  -p 'test_*.py' \
  -v
```

No third-party test framework is required.

### Unit test coverage

The current unit tests cover the following areas:

- Validation of `-R`, including invalid values, duplicate options, and invalid combinations.
- Generation-choice entropy calculations for passphrases with and without random-character insertion.
- Word-count selection for a requested generation-choice entropy target.
- Random-character insertion at the beginning, middle, and end of a word.
- Preservation of original word characters during insertion.
- Wordlist loading and removal of duplicate entries.
- Rejection of wordlists with fewer than two distinct entries.

The tests are intended to validate individual functions and argument-validation behavior without depending on specific randomly generated outputs.

### Integration testing

Unit tests do not fully validate the behavior of the complete command-line program. Integration tests should exercise the CLI as a subprocess and verify observable behavior.

Recommended integration-test coverage includes:

- Successful generation with `-p N`, including the exact word count.
- Correct handling of `-R 0`, `-R 1`, and `-R N`.
- Exactly `R` distinct word positions receiving one inserted character each.
- Preservation of each source word's characters after insertion.
- Correct behavior with custom separators and custom wordlists.
- Exit status and error messages for invalid arguments, missing files, and invalid wordlists.
- Agreement between the generated output and reported character counts, both including and excluding separators.
- `--passphrase -E BITS` meeting the target reported by the entropy calculation for different `-R` values.
- Separation of generated secrets on standard output from metadata on standard error.

Randomized tests should validate invariants rather than expect specific output strings. A test should not fail merely because a random word, character, or insertion position differs between executions.

**Entropy-test note:** Tests should distinguish the generator's calculated generation-choice entropy from the exact entropy of the final output string. The latter is not directly established by the current formula.

Run the test suite after changes to argument parsing, entropy calculations, wordlist handling, character insertion, or passphrase generation.

## Security considerations

### Randomness

`passgen` uses Python's `secrets` module, which is designed for generating cryptographically strong random values using the operating system's secure randomness source.

It does not use Python's ordinary `random` module for secret generation.

### Password distribution

Password generation uses rejection sampling: candidate strings are generated from the combined selected alphabet and rejected unless every selected class appears at least once. This produces a uniform distribution over the valid password space, assuming the underlying random selections are uniform.

### Wordlist quality

Passphrase entropy depends on the number of distinct entries and the uniform selection process. A large wordlist does not, by itself, guarantee that a passphrase is secure if the selection process is biased or the generated result is exposed.

The cleaner removes duplicates after normalization, but it does not assess word quality, predictability, or linguistic bias.

### Random-character insertion

The `-R` option increases the entropy of the generator's internal choices under the documented model. It does not guarantee a corresponding one-to-one increase in the entropy of the final output string.

Inserted characters are selected from the available insertion alphabet, excluding characters present in the configured separator. The separator itself remains fixed and does not contribute entropy.

### Handling generated secrets

- Avoid placing actual passwords directly in shell command arguments.
- Be careful when redirecting output to files, logs, clipboard managers, or other applications.
- Remember that terminal scrollback and shell pipelines may expose generated secrets.
- Do not commit generated credentials, private keys, or other secrets to version control.
- Use a reputable password manager to store generated passwords.

### Entropy is not a complete security guarantee

The reported entropy is a mathematical estimate based on the implemented generation model. It does not account for endpoint compromise, clipboard exposure, malware, insecure storage, or weaknesses in the service where a password is used.

## Command reference

### `passgen.py`

| Option | Description |
|---|---|
| `-a` | Include lowercase letters |
| `-A` | Include uppercase letters |
| `-0` | Include digits |
| `-!` | Include special characters |
| `-L N` | Generate a password of exactly `N` characters |
| `-E N` | Target at least `N` bits of entropy |
| `-p N` | Generate a passphrase containing exactly `N` words |
| `-R N` | Insert one random character into `N` distinct words; default: `0` |
| `--passphrase` | Explicitly select passphrase mode |
| `-d STRING` | Set the passphrase word separator; default: `-` |
| `--wordlist PATH` | Use a custom wordlist |
| `-h`, `--help` | Display usage information |

Exactly one of `-L` and `-E` must be supplied in password mode. In passphrase mode, choose either `-p` or `-E`; `--passphrase` is required when using `-E` without `-p`.

Character-class options cannot be combined with passphrase mode. Password and passphrase modes also cannot be mixed with each other.

When `-R` is used with `-p`, its value cannot exceed the word count. When used with `--passphrase -E`, the generator selects a word count sufficient to meet the target and accommodate the requested number of modified positions.

### `wordlist_cleaner.py`

| Option | Description |
|---|---|
| `INPUT` | Source wordlist file |
| `-o PATH`, `--output PATH` | Destination file; defaults to `INPUT.unique.txt` |
| `-h`, `--help` | Display usage information |

The cleaner requires an input path and never intentionally overwrites the source file. It preserves the first occurrence of each normalized entry and validates the written output.

## Examples

```bash
# Default password policy
passgen -L 32

# Password with a minimum entropy target
passgen -E 128

# Lowercase letters and digits only
passgen -a0 -L 24

# Uppercase and lowercase letters only
passgen -aA -E 128

# Six-word passphrase, hyphen-separated
passgen -p 6

# Six-word passphrase, space-separated
passgen -p 6 -d ' '

# Passphrase with at least 160 bits of estimated entropy
passgen --passphrase -E 160

# Insert a character into one word
passgen -p 6 -R 1

# Insert characters into two distinct words
passgen -p 6 -R 2

# Insert one character into every word
passgen -p 6 -R 6

# Target at least 128 bits of generation-choice entropy with insertion
passgen --passphrase -E 128 -R 2

# Passphrase using a custom wordlist
passgen -p 6 --wordlist ~/my-wordlist.txt

# Clean the default wordlist
python3 ~/scripts/shellutilities/passgen/wordlist_cleaner.py \
  ~/scripts/shellutilities/passgen/wordlist.csv

# Clean a wordlist to a specific destination
python3 ~/scripts/shellutilities/passgen/wordlist_cleaner.py \
  ~/scripts/shellutilities/passgen/wordlist.csv \
  --output ~/wordlists/wordlist.unique.txt

# Generate a passphrase using the cleaned wordlist
passgen --passphrase -E 128 \
  --wordlist ~/scripts/shellutilities/passgen/wordlist.unique.txt

# Run unit tests
python3 -m unittest discover \
  -s ~/scripts/shellutilities/passgen/tests \
  -v
```

## Limitations

- Maximum password length: 4096 characters.
- Maximum passphrase length: 4096 words.
- The number of modified words cannot exceed the generated word count.
- Wordlists must contain at least two distinct non-empty entries.
- Wordlists are line-based; CSV parsing is not performed.
- The cleaner normalizes case and Unicode representation, which can merge some distinct source entries.
- Entropy estimates rely on uniform random selection and the assumptions described above.
- Generation-choice entropy is not necessarily the exact entropy of the final passphrase string.
- Password generation requires at least one character from each selected class.
- Unit tests alone do not replace integration tests of the complete command-line interface.
