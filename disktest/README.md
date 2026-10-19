# disktest

A Bash utility for testing USB flash drives and other removable storage media on Linux using [F3 (Fight Flash Fraud)](https://github.com/AltraMayor/f3).

`disktest` provides two testing modes:

- **Non-destructive:** tests usable filesystem space by writing and verifying test data with `f3write` and `f3read`.
- **Destructive:** uses `f3probe` to check whether a device's usable capacity matches its advertised capacity.

The goal is to make validating new or suspicious storage media straightforward from the command line.

## Features

- Identifies the target device and displays its partitions, filesystems, sizes, and mount points.
- Tests mounted filesystems without formatting the device or intentionally overwriting existing files.
- Verifies written data and reports lost, corrupted, changed, or overwritten sectors through F3.
- Checks advertised versus usable capacity using the destructive testing mode.
- Requires explicit confirmation before running tests.
- Reports test results and propagates failure status through the function's exit code.

## Requirements

- Linux
- Bash
- `util-linux` (provides utilities such as `lsblk`, `findmnt`, and `mountpoint`)
- `F3` (`f3write`, `f3read`, and `f3probe`)

On Debian, Ubuntu, and derivatives:

```bash
sudo apt install f3 util-linux
```

## Installation

Add the `disktest` function to your `~/.bashrc`.

Reload your shell configuration:

```bash
source ~/.bashrc
```

Verify that the function is available:

```bash
type disktest
```

## Usage

### 1. Non-destructive filesystem test

```bash
disktest /dev/sdX
```

Replace `/dev/sdX` with the target device, such as `/dev/sdc`.

The function displays the device layout, asks for confirmation, and runs the following steps on each detected mounted filesystem:

1. `f3write` fills available filesystem space with test files.
2. `f3read` reads the test files and verifies their contents.
3. The function reports the result and returns a corresponding exit status.

Example:

```text
=== /dev/sdc1 — /media/user/FLASHDRIVE ===

--- Gravação ---
...

--- Leitura e verificação ---
...

RESULTADO: F3 sem erros reportados em /dev/sdc1

=== RESUMO ===
Sistemas de arquivos testados: 1
Falhas ou testes não executados: 0
```

**Important:** this mode can consume nearly all available free space. Existing files are not intentionally overwritten, but the test requires enough free space to write its test data. The generated `.h2w` files remain on the device after testing and must be removed when no longer needed.

### 2. Destructive capacity test

```bash
disktest --destructive /dev/sdX
```

This mode invokes:

```bash
sudo f3probe --destructive /dev/sdX
```

It requires the target device to be unmounted and asks the user to confirm the exact device path before proceeding.

Example output:

```text
Good news: The device `/dev/sdX' is the real thing

Device geometry:
        *Usable* size: 29.31 GB
       Announced size: 29.31 GB
               Module: 32.00 GB
```

This is a destructive operation. **All data on the selected device must be considered at risk.** Back up important data before running it, verify the device path carefully, and never run it against a disk containing data you need to preserve.

The destructive test is useful for detecting counterfeit-capacity devices without first filling an entire filesystem with test files. It is not a comprehensive physical-sector reliability test.

## Interpreting results

| Result | Meaning |
|---|---|
| `Data OK` | Data was read back correctly. |
| `Data LOST` | Written data could not be recovered correctly. |
| `Corrupted` | Data was corrupted. |
| `Slightly changed` | Data differs slightly from what was written. |
| `Overwritten` | Data was overwritten or otherwise failed verification. |
| Usable capacity below advertised capacity | May indicate counterfeit capacity or a device/layout issue; investigate further. |

A successful F3 test is evidence that the tested capacity behaved correctly during the test. It does not guarantee long-term reliability or rule out intermittent hardware faults.

## Limitations

- The non-destructive mode tests mounted filesystems, not every physical sector of the device.
- Unmounted partitions are not tested by the non-destructive mode.
- The destructive mode can destroy existing data and should only be used when that risk is acceptable.
- Neither mode is a comprehensive endurance, retention, or long-term reliability test.
- Results depend on the device, filesystem, operating system, and F3 version.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
