# KDBX Passkey Xtractor

Extracts WebAuthn passkey entries from a KeePassXC database into independent KDBX databases, generating a separate random master password for each one.

The program also creates a `vault-index.kdbx` database containing the original credential titles, the filenames of the individual databases, and their corresponding master passwords in protected KeePassXC fields.

The original database is never modified.

## Features

- Detects entries tagged `Passkey` using KeePassXC CLI.
- Skips passkey entries located in the Recycle Bin.
- Validates required passkey attributes before extraction.
- Fails closed if any active passkey candidate is invalid.
- Creates one independent KDBX database per valid passkey.
- Generates a random master password for each individual database.
- Generates random filenames with 128 bits of entropy.
- Creates a separate `vault-index.kdbx` with an independent master password.
- Stores individual database passwords in protected index entry fields.
- Preserves the original database's cryptographic settings by copying it rather than creating new databases from scratch.
- Validates each individual database and the final index.
- Does not export passkey private keys or credential secrets to plaintext files.
- Does not modify the source database.

## Requirements

### Software

- Python 3.
- `pexpect`.
- Flatpak.
- KeePassXC installed as a Flatpak application.

The tested KeePassXC Flatpak application ID is:

`org.keepassxc.KeePassXC`

The program invokes KeePassXC CLI through:

```bash
flatpak run --command=keepassxc-cli \
    org.keepassxc.KeePassXC
```

Install the Python dependency if necessary:

```bash
sudo apt install python3-pexpect
```

Install KeePassXC Flatpak if it is not already installed:

```bash
flatpak install flathub org.keepassxc.KeePassXC
```

## Installation

Clone the repository:

```bash
git clone <REPOSITORY_URL>
cd kdbx-passkey-xtractor
```

Ensure the script is executable:

```bash
chmod 700 extract_passkeys.py
```

Check Python syntax:

```bash
python3 -m py_compile extract_passkeys.py
```

## Usage

The program requires two positional arguments:

```text
python3 extract_passkeys.py SOURCE.kdbx OUTPUT_DIRECTORY
```

Example:

```bash
output_dir="passkeys-export-$(date +%Y%m%d-%H%M%S)"

python3 -u extract_passkeys.py \
    /path/to/original-database.kdbx \
    "$output_dir"
```

The output directory must not already exist.

### Password prompts

The program requests:

1. The original database master password.
2. A new master password for `vault-index.kdbx`.
3. Confirmation of the index master password.

The index password must be nonempty, match its confirmation, and differ from the original database password.

Individual database passwords are generated automatically.

They are not displayed during execution.

## Extraction workflow

### 1. Classification

The program opens the original database and searches for entries tagged `Passkey`.

Entries inside the Recycle Bin are skipped.

Each active candidate is checked for the required attributes:

**Protected attributes:**

- `KPEX_PASSKEY_CREDENTIAL_ID`
- `KPEX_PASSKEY_PRIVATE_KEY_PEM`

**Plain attribute:**

- `KPEX_PASSKEY_RELYING_PARTY`

The program also checks entry UUID validity and uniqueness.

If any active candidate is invalid, processing is aborted. This fail-closed behavior prevents incomplete or ambiguous passkeys from being silently ignored.

### 2. Individual database creation

For each valid passkey, the program:

1. Creates a copy of the original KDBX database.
2. Identifies the selected entry using its UUID.
3. Moves that entry to the database root.
4. Removes all other entries and groups from the copy.
5. Removes the Recycle Bin.
6. Changes the copied database's master password.
7. Validates the resulting database.

Each individual database must contain:

- One root group.
- One entry.
- One passkey.

The passkey's required attributes and UUID are checked again.

### 3. Password generation

Each individual database receives an independently generated password using Python's `secrets` module:

```python
secrets.token_urlsafe(32)
```

Each filename is generated using:

```python
secrets.token_hex(16) + ".kdbx"
```

This produces a filename containing 32 hexadecimal characters, representing 128 bits of randomness.

### 4. Vault index creation

The program creates `vault-index.kdbx` as a copy of the original database.

It clears the copied database and changes its master password to the new index password.

For each extracted passkey, it creates an index entry containing:

| Field | Content |
|---|---|
| Title | Original passkey entry title |
| UserName | Individual KDBX filename |
| Password | Individual KDBX master password |

The Password field is stored as a protected KeePassXC field.

The index does not contain the original passkey private keys.

### 5. Final validation

The program validates the index by checking:

- Database entry and group counts.
- Entry identification using the individual database filename.
- Original title and filename correspondence.
- Protected status of the Password field.
- Actual password correspondence between the index and the generated individual database passwords.

The final password comparison is performed internally. Passwords are not printed.

## Output structure

A successful extraction produces a directory similar to:

```text
passkeys-export-YYYYMMDD-HHMMSS/
├── 0123456789abcdef0123456789abcdef.kdbx
├── 1234567890abcdef1234567890abcdef.kdbx
├── 234567890abcdef1234567890abcdef.kdbx
└── vault-index.kdbx
```

Each randomly named KDBX contains exactly one extracted passkey.

`vault-index.kdbx` contains the information needed to identify and unlock the individual databases.

## Cryptographic settings

Individual databases and the index are created by copying the original KDBX database.

This preserves the source database's cryptographic configuration, including its cipher and key derivation function (KDF), instead of rebuilding databases with potentially different settings.

The program checks the cipher and KDF reported by KeePassXC during validation.

Configure the desired cryptographic settings in the original database before running the extraction.

## Security considerations

- The original database is opened but never intentionally modified.
- Passwords are not passed as command-line arguments or environment variables.
- Password prompts are handled through `pexpect` with terminal echo disabled.
- Generated passwords are kept in memory during processing.
- Passkey private keys and credential secrets are not exported to plaintext files.
- The output directory is created with permissions `0700`.
- Output KDBX files are created with permissions `0600`.
- Existing output directories and files are not overwritten.
- If processing fails, the program attempts to remove files created during that run.

Python cannot guarantee secure zeroization of immutable strings. Clearing references and variables reduces their lifetime but does not guarantee that secret data is erased from process memory.

File deletion through `unlink()` is also not a guarantee of secure physical erasure.

Keep the original database and a separate backup until the extracted databases have been independently checked.

## Important operational precautions

1. Back up the original KDBX before extraction.
2. Use a new, empty output directory for each run.
3. Preserve `vault-index.kdbx` and its master password.
4. Back up the complete output directory.
5. Verify that individual databases can be opened before relying on them.
6. Do not delete the original database until the extracted passkeys have been tested in their intended applications.

Losing the index or its master password can make recovery of the individual database passwords difficult or impossible.

## Failure behavior

The program aborts when it encounters:

- Invalid active passkey candidates.
- Missing or invalid required attributes.
- Duplicate entry UUIDs.
- Unexpected KeePassXC CLI responses.
- Database password or interaction failures.
- Unexpected database structure.
- Cryptographic configuration mismatches.
- Index population or validation failures.

On failure, the program attempts to remove files created during that execution. This cleanup does not guarantee secure erasure.

The original database remains untouched.

## Project scope

KDBX Passkey Xtractor is specifically intended to isolate KeePassXC passkey entries into independent KDBX databases and maintain a protected index of their passwords.

It is not intended to be a general-purpose KeePassXC backup, migration, or database synchronization utility.
