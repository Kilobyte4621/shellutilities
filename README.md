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

1. `add2bash`
2. `sh2txt`
3. `passgen`
4. `disktest`
5. `kdbx-passkey-xtractor`

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

Individual utilities may require Bash, Python, or external command-line tools and libraries. Refer to each utility's documentation for its specific requirements and installation instructions.

## Third-Party Dependencies

This repository may rely on external programs and libraries that are not distributed with the project.

Third-party components remain subject to their respective licenses and terms. The MIT License applies to the original code in this repository and does not replace or override the licenses of external dependencies.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
