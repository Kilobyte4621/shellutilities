# Shell Utilities

A collection of modular shell utilities for Bash configuration management, recursive script loading, and batch file conversion, alongside standalone command-line tools.

## General Philosophy

This repository focuses on practical, maintainable shell utilities with minimal dependencies and predictable behavior.

The tools address common workflow problems:

- **Shell configuration management:** Reduce manual `.bashrc` maintenance through centralized script loading and configurable exclusions.
- **Script interoperability:** Create text copies of shell scripts for documentation, code review, and sharing.
- **Password generation:** Generate passwords and memorable passphrases using configurable wordlists and character transformations.
- **Modularity:** Keep utilities independent so they can be used individually or integrated into existing workflows.

## Utilities

### 1. `add2bash` — v0.5.1

A Bash function for appending custom text to `~/.bashrc` or configuring a recursive shell script loader.

#### Features

- Append custom text to `~/.bashrc` with interactive confirmation.
- Generate `load_all.sh` to discover and source `.sh` files recursively.
- Exclude scripts using `.scriptignore` patterns.
- Optionally synchronize the auto-generated section of `.scriptignore` through `shellutilities/scriptignore-sync.sh`.
- Avoid duplicate custom text and loader configuration markers.
- Continue without automatic `.scriptignore` synchronization when the synchronization script is unavailable.

#### Usage

Source the function:

```bash
source ./add2bash/add2bash.sh
```

**Append custom text:**

```bash
add2bash 'alias ll="ls -lah"'
```

**Configure the recursive loader:**

Run the function from the directory containing the scripts you want to load:

```bash
cd ~/scripts/
add2bash
```

The function generates or overwrites `load_all.sh` in the current directory, then asks for confirmation before modifying `~/.bashrc`.

After accepting the configuration, reload the shell configuration:

```bash
source ~/.bashrc
```

#### `.scriptignore`

The generated loader reads exclusion patterns from `.scriptignore` in its root directory.

Examples:

```text
experimental.sh
/private/
/legacy/
```

Patterns without a leading `/` match substrings anywhere in a relative path. Patterns beginning with `/` match prefixes relative to the loader root.

Blank lines and lines beginning with `#` are ignored. These patterns are not full glob expressions or Git-style ignore rules.

#### Automatic synchronization

Version `v0.5.1` optionally invokes:

```bash
shellutilities/scriptignore-sync.sh --write
```

The synchronization script must exist and be executable at the expected path relative to the current working directory. If it is unavailable, synchronization is skipped.

**Security consideration:** The loader sources every discovered, readable `.sh` file that is not excluded. Only use it in directories containing scripts you trust.

See [`add2bash/`](add2bash/) for the utility's source code and documentation.

---

### 2. `sh2txt` — v0.1

A lightweight Bash function that copies `.sh` files to `.txt` files, preserving the original scripts.

#### Features

- Accepts a target directory as its first argument.
- Defaults to the current directory when no argument is supplied.
- Preserves filenames while replacing the `.sh` extension with `.txt`.
- Handles filenames containing spaces.
- Skips unmatched shell globs when no `.sh` files are present.
- Does not modify the original scripts.

#### Usage

Source the function:

```bash
source ./sh2txt/sh2txt.sh
```

**Convert files in the current directory:**

```bash
sh2txt
```

**Convert files in a specific directory:**

```bash
sh2txt ~/projects/my-scripts/
```

For example, `backup.sh` becomes `backup.txt` in the same directory.

The function is non-recursive by default. Only `.sh` files directly inside the specified directory are processed. A recursive alternative is included in the source code as a commented-out implementation.

Existing `.txt` files with matching names are overwritten, subject to filesystem permissions.

See [`sh2txt/`](sh2txt/) for the utility's source code and documentation.

---

### 3. `passgen`

A password and passphrase generator supporting configurable generation modes and wordlists.

The project includes functionality for generating passwords and memorable passphrases, with options for character transformations and entropy-oriented generation parameters.

See [`passgen/`](passgen/) for the implementation, wordlist resources, usage instructions, and documentation.

---

### 4. `disktest`

A Bash utility for testing USB flash drives and other removable storage media on Linux using [F3 (Fight Flash Fraud)](https://github.com/AltraMayor/f3).

#### Features

- Identify storage devices, partitions, filesystems, sizes, and mount points.
- Perform non-destructive filesystem testing using `f3write` and `f3read`.
- Detect data loss, corruption, unexpected changes, and overwritten test data.
- Perform destructive capacity verification using `f3probe`.
- Require explicit confirmation before testing.
- Report test results and propagate failures through the function's exit status.

#### Usage

**Non-destructive filesystem test:**

```bash
disktest /dev/sdX
```

Tests detected mounted filesystems by writing and verifying test data. Existing files are not intentionally overwritten, but the test can consume nearly all available free space. Generated `.h2w` files remain on the device until removed.

**Destructive capacity test:**

```bash
disktest --destructive /dev/sdX
```

Uses `f3probe` to compare advertised and usable device capacity. The target must be unmounted, and all data on the selected device must be considered at risk.

#### Requirements

- Linux and Bash
- `util-linux`
- F3 (`f3write`, `f3read`, and `f3probe`)

On Debian, Ubuntu, and derivatives:

```bash
sudo apt install f3 util-linux
```

**Limitations:** A successful test does not guarantee long-term reliability, endurance, or data retention. The non-destructive mode tests mounted filesystems rather than every physical sector; the destructive mode can destroy existing data.

See [`disktest/`](disktest/) for complete documentation and usage instructions.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Kilobyte4621/shellutilities.git
cd shellutilities
```

Source individual Bash utilities as needed, using their respective paths:

```bash
source ./add2bash/add2bash.sh
source ./sh2txt/sh2txt.sh
```

Adjust the filenames if they differ from those shown above. Source only the functions you intend to use.

Other utilities may have their own installation and execution requirements; consult their respective directories.

## Practical Examples

### Centralize shell configuration

Organize your shell scripts in a dedicated directory:

```text
~/scripts/
├── aliases.sh
├── functions.sh
├── git/
│   └── helpers.sh
└── development/
    └── tools.sh
```

Configure the loader from that directory:

```bash
cd ~/scripts/
source ~/scripts/shellutilities/add2bash/add2bash.sh
add2bash
```

After accepting the `.bashrc` modification, the generated loader discovers scripts recursively, subject to the `.scriptignore` rules.

To exclude a script, add a matching pattern to `~/scripts/.scriptignore`:

```text
development/tools.sh
```

### Create text copies of shell scripts

To prepare scripts for code review, documentation, or sharing:

```bash
source ./sh2txt/sh2txt.sh
sh2txt ~/projects/legacy-automation/
```

The function creates `.txt` copies beside the corresponding `.sh` files without modifying the originals.

## Dependencies

The Bash utilities rely on Bash and standard command-line utilities available on typical Linux systems. Optional `.scriptignore` synchronization requires the separate synchronization script.

Individual tools may have additional dependencies. Refer to their own documentation for details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
