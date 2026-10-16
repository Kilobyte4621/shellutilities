# Shell Utilities 🛠️

A robust collection of advanced, modular shell functions engineered to optimize environment synchronization, automate recursive script bootstrapping, and handle batch file interoperability smoothly across Linux environments.

---

## 📌 General Philosophy

In DevOps and local terminal environments, engineers face two recurring friction points:

1. **The `.bashrc` Clutter Problem:** Manually adding shortcuts, scripts, or multiple `source` lines creates maintenance nightmares and performance degradation over time.
2. **Platform Constraints & Code Portability:** Security configurations on modern platforms (like cloud environments or enterprise firewalls) frequently block the raw transfer or upload of executable `.sh` files, requiring rapid text extraction for Large Language Models (LLMs) or visual review.

This repository resolves these problems with zero external dependencies, emphasizing **idempotency** (running a tool multiple times without changing the result beyond the first application), **fail-safe defenses**, and strict cross-platform compatibility.

---

## 🚀 Deep-Dive Tool Documentation

### 1. `add2bash` (v0.5)

`add2bash` acts as a smart configuration injector and local environment manager for your main shell settings file (`~/.bashrc`). It features a dual-execution architectural path determined dynamically by user input.

```
                [Executed add2bash]
                        |
            /-----------------------\
     (Has Arguments)         (No Arguments)
           |                       |
   Inject Raw Custom       Generate Recursive
   Text to ~/.bashrc       Central 'load_all.sh'
                                   |
                           Verify .scriptignore
                                   |
                           Inject Entrypoint 
                             into ~/.bashrc

```

#### 🔹 Operational Frameworks

* **Mode A: Raw Text/Alias Appendment (Arguments Passed):** When executed with strings (e.g., `add2bash "alias k='kubectl'"`), the utility acts as a verified appender. It abstracts raw echo injections, showing a clean text preview and preventing malformed strings from ruining your environmental profile.
* **Mode B: Recursive Central Loader Bootstrapping (No Arguments):** When run standalone inside a directory containing shell scripts, it automatically compiles an isolated, executable script called `load_all.sh`. It then updates your system's `~/.bashrc` to source only this specific loader file exactly once.

#### 🔹 Technical Implementation Details

* **Deterministic Tracking & Idempotency:** The utility computes a dynamic target header tag signature: `# [add2bash] Central Loader for <Target_Path>`. Before running any write process, it runs a quiet structural lookup utilizing `grep -Fq`. If the sequence is found, it terminates early to avoid duplicate initialization paths.
* **Dynamic Sourcing Tree (`load_all.sh`):** The output module is pre-coded to query real-time execution locations dynamically via `readlink -f` combined with `$BASH_SOURCE` context mapping. It discovers all `.sh` extensions downward through a memory-safe `find` execution using null-byte line terminations (`-print0`) to avoid token-splitting issues on spaced filenames.
* **Advanced Cross-Platform `.scriptignore` Parser:** The generated loader reads matching ignore files line-by-line (`IFS= read -r line`). It strips raw Windows carriage returns (`\r`) automatically using `tr -d` and eliminates trailing shell whitespaces via `xargs`. This ensures your rules work flawlessly even if patterns are composed or edited on Windows platforms (CRLF line-ending format).
* **Infinite Execution-Loop Hardening:** Inside its runtime compilation shell loop, `add2bash` maps the filename variable against its own system runtime identity array (`$BASH_SOURCE`). If a match occurs, or if files lack explicit readable permissions (`! -r`), it triggers a shortcut `continue` instruction, ensuring the loader never tries to context-source itself recursively.
* **Interactive Approvals:** Destructive actions or files containing changes intended for target setup arrays are strictly halted beforehand by an internal validation function (`confirm_action`), waiting for a positive `[y/Y]` manual user interaction.

---

### 2. `sh2txt` (v0.1)

`sh2txt` is a quick batch utility designed to locate executable `.sh` files in a workspace and safely copy them into `.txt` extension replicas. This simplifies sharing script content with LLMs, pasting script blocks inside documentation repositories, or moving code through firewalls that flag `.sh` binaries.

#### 🔹 Operational Frameworks

* Automatically evaluates input directives. If a targeted path parameter is missing (`$1`), it targets the current working directory (`.`).
* Iterates sequentially through match targets without triggering breaking execution syntax errors.

#### 🔹 Technical Implementation Details

* **Zero Match Error Safeguard:** Standard directory loops fail or display system warnings if shell wildcards come up empty. `sh2txt` uses structural evaluation bounds (`[ -f "$f" ] || continue`) to safely bypass processing if no `.sh` files exist in the folder.
* **Native String Parameter Expansion:** Instead of spawning system overhead processes like `sed` or `awk` to change the filename extension, the code handles renames using native shell parameter expansion: `${f%.sh}.txt`. This isolates the trailing suffix, cleanly transforming `script.sh` into `script.txt`.
* **Built-in Scalability (Recursive Blueprint):** The tool includes a pre-built, alternative architecture commented out in the code. By toggling the comments, users can replace the single-tier directory loop with an advanced, multi-tier recursive engine powered by `find -exec sh -c 'for f; do cp -- "$f" "${f%.sh}.txt"; done' sh {} +`. This processes deeply nested scripts within an optimized subshell execution pattern.

---

## 🛠️ Quick Start & Integration Operations

### Step 1: Clone and Stage the Utilities

Download the script files into your chosen automation or local development path:

```bash
mkdir -p ~/scripts && cd ~/scripts 
git clone https://github.com/Kilobyte4621/shellutilities.git
cd shellutilities

```

### Step 2: Immediate Interventions (On-The-Fly Sourcing)

Because these utilities are written as lightweight shell functions rather than standalone binaries, they must be sourced directly into your active session environment to be registered:

```bash
source add2bash.sh
source sh2txt.sh

```

---

## 💡 Real-World Use Case Scenarios

### Scenario A: Bootstrapping a Recursive Config Toolkit

Imagine you have a custom toolkit folder located at `~/scripts/` containing multiple separate shell files (`aliases.sh`, `docker-helpers.sh`, `git-hacks.sh`). These scripts can be organized into subfolders, mixed structures, or completely different cloned git repositories. Because `load_all.sh` runs recursively down your directory tree, everything gets gathered dynamically.

Instead of manual indexing inside your main profile, execute `add2bash` directly:

```bash
# 1. Navigate to your custom automation directory
cd ~/scripts/

# 2. Fire up the automatic generator
add2bash

```

If you skipped **Step 2** of the Quick Start and want to trigger the utility without executing it across your global profile yet, simply source the function container on the fly before running the generator:

```bash
# Alternate 2: Source the container directly to call the function instantly
source ~/scripts/shellutilities/add2bash.sh && add2bash

```

**What Happens Behind the Scenes:**

1. `add2bash` recognizes that no extra text arguments were passed.
2. It compiles a highly stable `load_all.sh` utility within that directory.
3. It prints a clear preview of the changes it wants to make to your `~/.bashrc`.
4. Once you approve the prompt (`y`), it adds a safe, single-line configuration hook.

If you want to temporarily disable a script (like `experimental.sh`), simply add it to a local exclusion list:

```bash
echo "experimental.sh" >> .scriptignore

```

The next time you open a terminal window, `load_all.sh` will skip that script entirely.

### Scenario B: Batch Preparing Scripts for LLM Prompt Analysis

When you need an AI tool to audit or refactor a group of scripts inside a project directory, use `sh2txt` to quickly generate text-friendly copies:

```bash
# Convert all .sh files inside a specific project folder
sh2txt ~/projects/legacy-automation/

```

This leaves your primary executable scripts untouched while creating matching `.txt` files right next to them, ready to be grouped or attached to your prompt window.

***

# passgen

**A cryptographically secure password and passphrase generator for the command line.**

`passgen` is a lightweight Python utility for generating random passwords and passphrases using Python's `secrets` module. It supports configurable character classes, minimum entropy targets, custom wordlists, and selectable word separators.

The goal is to provide secure defaults for everyday use while keeping customization straightforward.

## Features

- Cryptographically secure random selection using Python's `secrets` module.
- Four character classes for passwords: lowercase letters, uppercase letters, digits, and special characters.
- All four character classes enabled by default for password generation.
- Optional character-class selection for custom password policies.
- Password generation by exact length or minimum entropy target.
- Passphrase generation by exact word count or minimum entropy target.
- Custom wordlists and configurable passphrase separators.
- UTF-8 wordlists supported, including files with a UTF-8 BOM.
- Duplicate word entries removed automatically.
- Passwords and passphrases written to standard output; metadata written to standard error.
- No third-party Python dependencies.

## Requirements

- Python 3.8 or newer.
- A Unix-like environment with a shell for the provided wrapper.

The Python script can also be invoked directly on systems where Python 3 is available.

## Installation

Clone or copy the repository into your preferred scripts directory. For example:

```bash
mkdir -p ~/scripts/shellutilities/passgen
```

Place the following files in the `passgen` directory:

```text
passgen/
├── passgen.py
├── passgen.sh
└── wordlist.csv
```

Make the Python script executable:

```bash
chmod +x ~/scripts/shellutilities/passgen/passgen.py
```

The provided shell wrapper defines a `passgen` function that invokes the Python script. If your shell automatically loads functions from `~/scripts`, ensure the wrapper is loaded by your shell configuration.

Alternatively, invoke the Python script directly:

```bash
python3 ~/scripts/shellutilities/passgen/passgen.py -L 32
```

Check the available options:

```bash
passgen --help
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

### Entropy target

Use `--passphrase -E` to request a minimum passphrase entropy:

```bash
passgen --passphrase -E 128
```

The generator calculates the number of words needed to meet the target, rounding up to the next whole word.

For example, if the wordlist contains 46,201 distinct words, each independently selected word contributes approximately 15.50 bits of entropy. A 128-bit target therefore requires nine words, providing approximately 139.46 bits.

The number of words is limited to 4096.

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

Wordlists must be valid UTF-8 text and contain at least two distinct non-empty entries. UTF-8 files with or without a byte-order mark (BOM) are supported. Blank lines are ignored, duplicate entries are removed, and punctuation within entries is preserved.

For reliable entropy estimates, use a wordlist with sufficient size and entries appropriate for your intended use. Avoid wordlists with predictable or heavily biased content.

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

### Passphrase entropy

For a wordlist containing \(W\) distinct entries and a passphrase containing \(n\) independently selected words, the estimated entropy is:

\[
H = n\log_2(W)
\]

This calculation assumes each distinct entry has an equal probability of selection, words are selected independently, and repetition is allowed.

The separator does not contribute entropy because it is fixed by the user.

### Interpreting the output

The generated password or passphrase is printed to standard output. Information about length or word count, wordlist size, and estimated entropy is printed to standard error.

For example:

```text
Length: 32 characters | Entropy: 205.07 bits
```

This separation allows the generated secret to be captured independently from the metadata.

## Security considerations

### Randomness

`passgen` uses Python's `secrets` module, which is designed for generating cryptographically strong random values using the operating system's secure randomness source.

It does not use Python's ordinary `random` module for secret generation.

### Password distribution

Password generation uses rejection sampling: candidate strings are generated from the combined selected alphabet and rejected unless every selected class appears at least once. This produces a uniform distribution over the valid password space, assuming the underlying random selections are uniform.

### Wordlist quality

Passphrase entropy depends on the number of distinct entries and the uniform selection process. A large wordlist does not, by itself, guarantee that a passphrase is secure if the selection process is biased or the generated result is exposed.

### Handling generated secrets

- Avoid placing actual passwords directly in shell command arguments.
- Be careful when redirecting output to files, logs, clipboard managers, or other applications.
- Remember that terminal scrollback and shell pipelines may expose generated secrets.
- Do not commit generated credentials, private keys, or other secrets to version control.
- Use a reputable password manager to store generated passwords.

### Entropy is not a complete security guarantee

The reported entropy is a mathematical estimate based on the implemented generation model. It does not account for endpoint compromise, clipboard exposure, malware, insecure storage, or weaknesses in the service where a password is used.

## Command reference

| Option | Description |
|---|---|
| `-a` | Include lowercase letters |
| `-A` | Include uppercase letters |
| `-0` | Include digits |
| `-!` | Include special characters |
| `-L N` | Generate a password of exactly `N` characters |
| `-E N` | Target at least `N` bits of entropy |
| `-p N` | Generate a passphrase containing exactly `N` words |
| `--passphrase` | Explicitly select passphrase mode |
| `-d STRING` | Set the passphrase word separator; default: `-` |
| `--wordlist PATH` | Use a custom wordlist |
| `-h`, `--help` | Display usage information |

Exactly one of `-L` and `-E` must be supplied in password mode. In passphrase mode, choose either `-p` or `-E`; `--passphrase` is required when using `-E` without `-p`.

Character-class options cannot be combined with passphrase mode. Password and passphrase modes also cannot be mixed with each other.

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

# Passphrase using a custom wordlist
passgen -p 6 --wordlist ~/my-wordlist.txt
```

## Limitations

- Maximum password length: 4096 characters.
- Maximum passphrase length: 4096 words.
- Wordlists must contain at least two distinct non-empty entries.
- The passphrase wordlist is line-based; CSV parsing is not performed.
- Entropy estimates rely on uniform random selection and the assumptions described above.
- Password generation requires at least one character from each selected class.

## License

Add the project's chosen license here before distributing the software. If the project already has a repository-level license, refer to that license instead.
