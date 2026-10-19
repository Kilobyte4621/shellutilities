# add2bash

A Bash utility that configures a recursive shell script loader or appends custom text to `~/.bashrc`.

## Features

- **Custom `.bashrc` entries:** Append arbitrary text to `~/.bashrc` with user confirmation.
- **Recursive script loading:** Generate `load_all.sh` to discover and source `.sh` files recursively from the current directory.
- **`.scriptignore` support:** Exclude scripts using patterns defined in the root `.scriptignore` file.
- **Automatic `.scriptignore` synchronization:** Optionally invoke `shellutilities/scriptignore-sync.sh` to regenerate the auto-generated section of `.scriptignore` from `# scriptignore: skip` directives in shell scripts.
- **Idempotency checks:** Avoid appending identical custom text or duplicate loader configuration markers.
- **User confirmation:** Request confirmation before modifying `~/.bashrc`.
- **Graceful fallback:** Continue without synchronizing `.scriptignore` when the synchronization script is missing.
- **Standalone execution:** Define `add2bash` for reuse or execute the file directly as a command.

## Requirements

- Bash
- Standard utilities: `grep`, `find`, `readlink`, `tr`, `xargs`, `cat`, `chmod`, and `sed`
- A writable `~/.bashrc`
- Optional: an executable `shellutilities/scriptignore-sync.sh` for automatic `.scriptignore` synchronization

## Usage

Run the script directly:

```bash
chmod +x add2bash.sh
./add2bash.sh
```

### 1. Configure the recursive loader

Run `add2bash.sh` without arguments from the root directory containing your shell scripts.

The utility generates or overwrites `load_all.sh` in the current directory and attempts to synchronize `.scriptignore` if the optional synchronization script exists and is executable.

After displaying the proposed `.bashrc` modification, it asks for confirmation. If accepted, it appends a block that sources `load_all.sh` whenever Bash reads `~/.bashrc`.

Start a new interactive shell or reload the configuration:

```bash
source ~/.bashrc
```

### 2. Append custom text to `.bashrc`

Pass the desired text as the first argument:

```bash
./add2bash.sh 'alias ll="ls -lah"'
```

The utility checks whether the exact text already exists in `~/.bashrc`, displays the proposed addition, and requests confirmation before appending it.

For multiline content, pass a single argument containing the desired line breaks.

## Recursive loader

The generated `load_all.sh`:

1. Determines its own directory and uses it as the loader root.
2. Reads ignore patterns from the root `.scriptignore`, if the file exists and is readable.
3. Discovers `.sh` files recursively using `find`.
4. Skips the loader itself, non-regular files, and unreadable files.
5. Checks each script's relative path against the ignore patterns.
6. Sources scripts that are not excluded.

### `.scriptignore` patterns

Patterns are interpreted as literal Bash substring matches, not regular expressions or full glob expressions.

| Pattern | Behavior |
|---|---|
| `example.sh` | Excludes paths containing `example.sh`. |
| `utilities` | Excludes paths containing `utilities`. |
| `/private/` | Excludes paths whose relative names start with `private/`. |
| `/config.sh` | Excludes paths whose relative names start with `config.sh`. |

**Important:** A pattern beginning with `/` is matched against the beginning of the path relative to the loader root, after removing the leading slash. Other patterns match anywhere in the relative path. A root-anchored pattern is a prefix match, not an exact path match.

Blank lines and lines beginning with `#` are ignored. Leading and trailing whitespace is removed from patterns.

## Automatic `.scriptignore` synchronization

Version `v0.5.1` adds optional integration with:

```text
shellutilities/scriptignore-sync.sh
```

When this executable is present under the current working directory, `add2bash.sh` runs:

```bash
shellutilities/scriptignore-sync.sh --write
```

The synchronization script is responsible for regenerating the auto-generated section of `.scriptignore` using `# scriptignore: skip` directives found in `.sh` files under the loader root.

If the synchronization script is missing, the utility skips synchronization and continues with the loader setup. If synchronization fails, it prints a warning and continues.

## Version history

### v0.5.1

- Added optional synchronization of the auto-generated `.scriptignore` section.
- Added graceful fallback when the synchronization script is missing.
- Preserved the previous `v0.5` behavior when synchronization is unavailable.

## Limitations and considerations

- **Current working directory matters:** The directory from which `add2bash.sh` is executed determines where `load_all.sh` is generated and which directory is scanned.
- **Existing loader replacement:** Running the utility again overwrites the existing `load_all.sh` in the current directory.
- **Partial idempotency:** Duplicate checks prevent repeated insertion of the same custom text or loader marker, but do not update an existing loader block when its path or configuration changes.
- **Sourcing executes code:** Every non-ignored, readable `.sh` file discovered by the loader is executed in the current shell. Scripts can change environment variables, define functions, alter shell options, or perform other actions. Only use this loader with scripts you trust.
- **Ignore patterns are not Git-style rules:** There is no support for negation, wildcard expansion, or directory-specific matching semantics beyond the documented substring and prefix behavior.
- **Synchronization failures are non-fatal:** A failed `.scriptignore` synchronization does not automatically abort loader generation or prevent the subsequent `.bashrc` setup.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
