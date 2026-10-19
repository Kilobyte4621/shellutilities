# sh2txt

A lightweight Bash function that copies `.sh` files as `.txt` files, preserving their contents and filenames except for the file extension.

## Features

- **Directory argument:** Accepts a target directory as its first argument.
- **Current directory fallback:** Defaults to the current directory (`.`) when no argument is provided.
- **Extension replacement:** Creates a `.txt` copy of each `.sh` file, preserving the original script.
- **Safe filename handling:** Supports filenames containing spaces and other characters handled by quoted shell arguments.
- **Empty-directory handling:** Skips nonexistent matches when no `.sh` files are found, avoiding unnecessary `cp` errors.
- **Non-recursive operation:** Processes only `.sh` files directly inside the specified directory.

## Requirements

- Bash
- `cp` (GNU Coreutils or a compatible implementation)

## Installation

Add the function to your shell configuration or save it in a script that you source.

For example, save it as `sh2txt.sh` and load it into the current shell:

```bash
source sh2txt.sh
```

## Usage

### Convert files in the current directory

```bash
sh2txt
```

### Convert files in a specific directory

```bash
sh2txt /path/to/scripts
```

### Example

Given the following directory:

```text
scripts/
├── backup.sh
├── cleanup.sh
└── utilities/
    └── helper.sh
```

Running:

```bash
sh2txt scripts
```

Produces:

```text
scripts/
├── backup.sh
├── backup.txt
├── cleanup.sh
├── cleanup.txt
└── utilities/
    └── helper.sh
```

The original `.sh` files remain unchanged. The `utilities/` subdirectory is not processed.

## Behavior and limitations

- Only files matching `*.sh` directly inside the target directory are processed.
- Subdirectories are not traversed.
- Each output file uses the original filename with `.txt` replacing `.sh`.
- If a corresponding `.txt` file already exists, `cp` overwrites it, subject to filesystem permissions and other applicable restrictions.
- If the target directory does not exist or cannot be accessed, errors may be reported by the shell or `cp`.
- The function does not explicitly validate that the supplied path is a directory.

## Recursive alternative

A recursive implementation is included as a commented-out alternative in the source code. To enable recursive conversion, replace the non-recursive loop with the provided `find`-based implementation.

## Version history

### v0.1

- Added support for an optional directory argument.
- Defaults to the current directory when no argument is supplied.
- Skips unmatched `.sh` patterns instead of attempting to copy nonexistent files.
- Preserves the original shell scripts.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
