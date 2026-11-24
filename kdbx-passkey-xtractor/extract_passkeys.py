#!/usr/bin/env python3

# Version Details: v0.0.1
# - Extracts passkeys of a .kdbx database into separate daabases, preserving original cryptographic settings.

import getpass
import os
import re
import secrets
import shutil
import sys
import uuid

import pexpect


PROMPT = re.compile(r"(?m)^[^\r\n]*> ")

REQUIRED_PROTECTED = {
    "KPEX_PASSKEY_CREDENTIAL_ID",
    "KPEX_PASSKEY_PRIVATE_KEY_PEM",
}

REQUIRED_PLAIN = {
    "KPEX_PASSKEY_RELYING_PARTY",
}

REQUIRED_ATTRIBUTES = REQUIRED_PROTECTED | REQUIRED_PLAIN


def quote_path(path):
    if "\n" in path or "\r" in path or "\0" in path:
        raise ValueError("Unsupported path.")

    return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


def cli_open(database, password):
    child = pexpect.spawn(
        "flatpak",
        [
            "run",
            "--command=keepassxc-cli",
            "org.keepassxc.KeePassXC",
            "open",
            database,
        ],
        encoding="utf-8",
        timeout=120,
        env={"TERM": "dumb", "NO_COLOR": "1"},
    )

    child.setecho(False)
    child.expect("Enter password to unlock")
    child.sendline(password)
    child.expect(PROMPT)

    return child


def cli_command(child, command):
    child.sendline(command)
    child.expect(PROMPT)

    output = child.before
    lines = output.splitlines()

    # Remove o comando ecoado pelo terminal, se presente.
    if lines and lines[0].strip() == command:
        lines.pop(0)

    return "\n".join(lines)

def cli_close(child):
    if child is None or not child.isalive():
        return

    child.sendline("exit")
    child.expect(pexpect.EOF)
    child.close()

    if child.exitstatus != 0:
        raise RuntimeError("KeePassXC exited unsuccessfully.")


def extract_uuid(output):
    values = []

    for line in output.splitlines():
        name, separator, value = line.partition(":")

        if separator and name.strip() == "Uuid":
            values.append(value.strip())

    if len(values) != 1:
        return None

    raw = values[0]

    if not (raw.startswith("{") and raw.endswith("}")):
        return None

    try:
        return str(uuid.UUID(raw[1:-1]))
    except ValueError:
        return None


def inspect_passkey(output):
    attributes = {}

    for line in output.splitlines():
        name, separator, value = line.partition(":")

        if separator and name.strip() in REQUIRED_ATTRIBUTES:
            attributes.setdefault(name.strip(), []).append(value.strip())

    missing = []
    invalid = []
    duplicates = []

    for name in REQUIRED_ATTRIBUTES:
        values = attributes.get(name, [])

        if not values:
            missing.append(name)
            continue

        if len(values) != 1:
            duplicates.append(name)
            continue

        value = values[0]

        if name in REQUIRED_PROTECTED and value != "PROTECTED":
            invalid.append(name)

        elif name in REQUIRED_PLAIN and (
            not value or value == "PROTECTED"
        ):
            invalid.append(name)

    return (
        missing,
        invalid,
        duplicates,
        extract_uuid(output),
    )


def field_map(output):
    fields = {}

    for line in output.splitlines():
        name, separator, value = line.partition(":")

        if separator:
            fields.setdefault(name.strip(), []).append(value.strip())

    return fields


def parse_db_info(output):
    result = {}

    for key in ("Cipher", "KDF"):
        match = re.search(
            rf"^{key}:\s*(.+)$",
            output,
            re.MULTILINE,
        )

        if not match:
            raise RuntimeError("Could not read database crypto settings.")

        result[key] = match.group(1).strip()

    for key in ("Number of groups", "Number of entries", "Number of passkeys"):
        match = re.search(
            rf"^{re.escape(key)}:\s*(\d+)$",
            output,
            re.MULTILINE,
        )

        if match:
            result[key] = int(match.group(1))

    return result


def list_items(child):
    output = cli_command(child, "ls -f /")

    items = [
        line.strip()
        for line in output.splitlines()
        if line.strip()
    ]

    if items == ["[empty]"]:
        return []

    return items

def classify_original(database, password):
    child = None

    try:
        child = cli_open(database, password)

        info = parse_db_info(cli_command(child, "db-info"))

        search_output = cli_command(child, "search +tag:Passkey")

        paths = [
            line.strip()
            for line in search_output.splitlines()
            if line.strip().startswith("/")
        ]

        active_paths = [
            path for path in paths
            if path != "/Recycle Bin"
            and not path.startswith("/Recycle Bin/")
        ]

        recycled = len(paths) - len(active_paths)

        if recycled:
            print(f"Skipped {recycled} recycled candidate(s).")

        if not active_paths:
            raise RuntimeError("No active Passkey entries found.")

        if len(active_paths) != len(set(active_paths)):
            raise RuntimeError("Ambiguous duplicate entry paths.")

        valid = []
        seen_uuids = set()
        invalid_count = 0

        for number, path in enumerate(active_paths, start=1):
            output = cli_command(
                child,
                "show --all " + quote_path(path),
            )

            if "Title:" not in output:
                first_line = output.splitlines()[0] if output.splitlines() else "<empty>"
                response_type = (
                    "CLI error"
                    if "Could not" in first_line or "Error" in first_line
                    else "unexpected response"
                )
                raise RuntimeError(
                    f"Root entry inspection failed ({response_type}; "
                    f"response length: {len(output)} characters)."
                )

            missing, invalid, duplicates, entry_uuid = (
                inspect_passkey(output)
            )

            errors = []

            if missing:
                errors.append("incomplete")

            if invalid:
                errors.append("invalid protection")

            if duplicates:
                errors.append("duplicate attributes")

            if entry_uuid is None:
                errors.append("invalid UUID")

            elif entry_uuid in seen_uuids:
                errors.append("duplicate UUID")

            else:
                seen_uuids.add(entry_uuid)

            if errors:
                invalid_count += 1
                print(f"Entry {number}: INVALID ({', '.join(errors)}).")
                continue

            title_values = field_map(output).get("Title", [])

            if len(title_values) != 1 or not title_values[0]:
                raise RuntimeError("Passkey title validation failed.")

            valid.append((path, entry_uuid, title_values[0]))
            print(f"Entry {number}: structurally valid.")

        print(f"Active candidates: {len(active_paths)}")
        print(f"Valid entries: {len(valid)}")
        print(f"Invalid entries: {invalid_count}")

        if invalid_count:
            raise RuntimeError("FAIL-CLOSED: processing aborted.")

        return valid, info

    finally:
        if child is not None:
            if child.isalive():
                child.close(force=True)


def create_copy(source, destination):
    fd = os.open(
        destination,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    os.close(fd)

    try:
        shutil.copyfile(source, destination)
        os.chmod(destination, 0o600)
    except Exception:
        try:
            os.unlink(destination)
        except OSError:
            pass
        raise


def change_database_password(database, old_password, new_password):
    child = pexpect.spawn(
        "flatpak",
        [
            "run", "--command=keepassxc-cli",
            "org.keepassxc.KeePassXC",
            "db-edit", "--set-password", database,
        ],
        encoding="utf-8",
        timeout=180,
        env={"TERM": "dumb", "NO_COLOR": "1"},
    )

    try:
        child.setecho(False)

        child.expect(
            r"(?i)(current database password|enter password to unlock)"
        )
        child.sendline(old_password)

        child.expect(
            r"(?i)(new database password|enter password to encrypt database)"
        )
        child.sendline(new_password)

        child.expect(r"(?i)repeat (new )?password")
        child.sendline(new_password)

        child.expect(pexpect.EOF)

        output = child.before or ""
        child.close()

        if child.exitstatus != 0:
            raise RuntimeError("Database password change failed.")

        if "successfully" not in output.lower():
            raise RuntimeError("Password change was not confirmed.")

    finally:
        if child.isalive():
            child.close(force=True)

def verify_individual(database, password, target_uuid, crypto):
    child = None

    try:
        child = cli_open(database, password)

        info = parse_db_info(cli_command(child, "db-info"))

        if (
            info.get("Number of groups") != 1
            or info.get("Number of entries") != 1
            or info.get("Number of passkeys") != 1
            or info.get("Cipher") != crypto["Cipher"]
            or info.get("KDF") != crypto["KDF"]
        ):
            raise RuntimeError("Individual database validation failed.")

        items = list_items(child)

        if len(items) != 1 or items[0].endswith("/"):
            raise RuntimeError("Unexpected individual database contents.")

        output = cli_command(
            child,
            "show --all " + quote_path(items[0]),
        )

        missing, invalid, duplicates, found_uuid = inspect_passkey(output)

        if (
            missing
            or invalid
            or duplicates
            or found_uuid != target_uuid
        ):
            raise RuntimeError("Individual passkey validation failed.")

    finally:
        if child is not None and child.isalive():
            child.close(force=True)


def clear_index_database(database, password):
    child = None

    try:
        child = cli_open(database, password)

        items = list_items(child)

        for item in items:
            if item.endswith("/"):
                continue

            result = cli_command(
                child,
                "rm " + quote_path(item),
            )

            if "Successfully recycled entry" not in result:
                raise RuntimeError("Could not clear index entry.")

        for item in items:
            if not item.endswith("/"):
                continue

            group = item[:-1]

            if group == "Recycle Bin":
                continue

            result = cli_command(
                child,
                "rmdir " + quote_path(group),
            )

            if "Successfully recycled group" not in result:
                raise RuntimeError("Could not clear index group.")

        remaining = list_items(child)

        if "Recycle Bin/" in remaining:
            result = cli_command(child, 'rmdir "Recycle Bin"')

            if "Successfully deleted group Recycle Bin" not in result:
                raise RuntimeError("Could not clear index recycle bin.")

        remaining = list_items(child)

        if remaining:
            raise RuntimeError(
                f"Index database is not empty. Remaining items: {remaining!r}"
            )

    finally:
        if child is not None and child.isalive():
            child.close(force=True)


def add_index_entry(database, index_password, title, filename, entry_password):
    child = pexpect.spawn(
        "flatpak",
        [
            "run", "--command=keepassxc-cli",
            "org.keepassxc.KeePassXC",
            "add",
            "--username", filename,
            "--password-prompt",
            database,
            title,
        ],
        encoding="utf-8",
        timeout=180,
        env={"TERM": "dumb", "NO_COLOR": "1"},
    )

    try:
        child.setecho(False)

        child.expect("Enter password to unlock")
        child.sendline(index_password)

        child.expect("Enter password for new entry")
        child.sendline(entry_password)

        child.expect(pexpect.EOF)

        output = child.before or ""
        child.close()

        if child.exitstatus != 0:
            raise RuntimeError("Could not add index entry.")

        if "successfully" not in output.lower():
            raise RuntimeError("Index entry creation was not confirmed.")

    finally:
        if child.isalive():
            child.close(force=True)


def validate_index(database, password, records):
    child = None

    try:
        child = cli_open(database, password)

        info = parse_db_info(cli_command(child, "db-info"))

        if (
            info.get("Number of entries") != len(records)
            or info.get("Number of groups") != 1
        ):
            raise RuntimeError("Index database counts are incorrect.")

        for record in records:
            filename = record["filename"]

            search_output = cli_command(
                child,
                "search " + quote_path(filename),
            )

            paths = [
                line.strip()
                for line in search_output.splitlines()
                if line.strip().startswith("/")
            ]

            matches = []

            for path in paths:
                output = cli_command(
                    child,
                    "show --all " + quote_path(path),
                )

                fields = field_map(output)

                if fields.get("UserName") == [filename]:
                    matches.append((path, fields))

            if len(matches) != 1:
                raise RuntimeError("Index entry identification failed.")

            path, fields = matches[0]

            if (
                fields.get("Title") != [record["title"]]
                or fields.get("UserName") != [filename]
                or fields.get("Password") != ["PROTECTED"]
            ):
                raise RuntimeError("Index entry metadata validation failed.")

            # Read the protected password into memory, without displaying it.
            protected_output = cli_command(
                child,
                "show --show-protected " + quote_path(path),
            )

            protected_fields = field_map(protected_output)

            if protected_fields.get("Password") != [record["password"]]:
                raise RuntimeError("Index password mapping validation failed.")

    finally:
        if child is not None and child.isalive():
            child.close(force=True)


def isolate_entry(database, password, source_path, target_uuid, crypto):
    child = None

    try:
        child = cli_open(database, password)

        # Confirm that the copied entry is the intended credential.
        before = cli_command(
            child,
            "show --all " + quote_path(source_path),
        )

        if "Title:" not in before:
            raise RuntimeError("Selected entry not found in copy.")

        if extract_uuid(before) != target_uuid:
            raise RuntimeError("Selected entry UUID mismatch.")

        missing, invalid, duplicates, found_uuid = inspect_passkey(before)

        if missing or invalid or duplicates or found_uuid != target_uuid:
            raise RuntimeError("Selected passkey validation failed.")


        # Move the selected entry to the database root.
        result = cli_command(
            child,
            "mv " + quote_path(source_path) + " /",
        )

        if "Successfully moved entry" not in result:
            raise RuntimeError("Could not move selected entry.")

        # Inspect all root entries and identify the selected one by UUID.
        items = list_items(child)

        normalized_names = [
            item[:-1] if item.endswith("/") else item
            for item in items
        ]

        if len(normalized_names) != len(set(normalized_names)):
            raise RuntimeError("Ambiguous root entry names.")

        selected_item = None
        selected_count = 0

        # Remove all other root-level entries.
        for item in items:
            if item.endswith("/"):
                continue

            output = cli_command(
                child,
                "show --all " + quote_path(item),
            )

            if "Title:" not in output:
                first_line = (
                    output.splitlines()[0]
                    if output.splitlines()
                    else "<empty>"
                )

                safe_line = first_line.replace(item, "<entry>")

                print(f"CLI response: {safe_line!r}")
                raise RuntimeError("Root entry inspection failed.")

            current_uuid = extract_uuid(output)

            if current_uuid is None:
                raise RuntimeError("Root entry UUID validation failed.")

            if current_uuid == target_uuid:
                selected_item = item
                selected_count += 1
            else:
                result = cli_command(
                    child,
                    "rm " + quote_path(item),
                )

                if "Successfully recycled entry" not in result:
                    raise RuntimeError("Could not remove another entry.")

        if selected_count != 1 or selected_item is None:
            raise RuntimeError("Selected entry was not uniquely identified.")

        # Remove all other root-level groups.
        for item in items:
            if not item.endswith("/"):
                continue

            group_name = item[:-1]

            if group_name == "Recycle Bin":
                continue

            result = cli_command(
                child,
                "rmdir " + quote_path(group_name),
            )

            if "Successfully recycled group" not in result:
                raise RuntimeError("Could not remove a group.")

        # Permanently delete the recycle bin, if it exists.
        remaining = list_items(child)

        if "Recycle Bin/" in remaining:
            result = cli_command(child, 'rmdir "Recycle Bin"')

            if "Successfully deleted group Recycle Bin" not in result:
                raise RuntimeError("Could not delete recycle bin.")

        # Verify that only the selected root entry remains.
        remaining = list_items(child)

        if remaining != [selected_item]:
            raise RuntimeError("Unexpected entries remain in database.")

        final_info = parse_db_info(
            cli_command(child, "db-info")
        )

        if (
            final_info.get("Number of groups") != 1
            or final_info.get("Number of entries") != 1
            or final_info.get("Number of passkeys") != 1
        ):
            raise RuntimeError("Final database counts are incorrect.")

        if (
            final_info.get("Cipher") != crypto["Cipher"]
            or final_info.get("KDF") != crypto["KDF"]
        ):
            raise RuntimeError("Cryptographic settings changed.")

        # Verify the selected entry and its visible metadata again.
        after = cli_command(
            child,
            "show --all " + quote_path(selected_item),
        )

        missing, invalid, duplicates, final_uuid = inspect_passkey(after)

        hash_matches = field_map(before) == field_map(after)

        before_fields = field_map(before)
        after_fields = field_map(after)

        changed_fields = sorted(
            key
            for key in set(before_fields) | set(after_fields)
            if before_fields.get(key) != after_fields.get(key)
        )


        if (
            missing
            or invalid
            or duplicates
            or final_uuid != target_uuid
            or not hash_matches
        ):
            raise RuntimeError("Final entry integrity check failed.")

    finally:
        if child is not None:
            if child.isalive():
                child.close(force=True)



def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} SOURCE.kdbx OUTPUT_DIRECTORY")
        return 2

    source = os.path.abspath(sys.argv[1])
    output_dir = os.path.abspath(sys.argv[2])

    if not os.path.isfile(source) or os.path.islink(source):
        print("Source must be a regular, non-symlink file.")
        return 1

    password = None
    index_password = None
    records = []
    created_files = []
    directory_created = False
    stage = "initialization"
    success = False

    try:
        password = getpass.getpass("Database password: ")

        stage = "classification"
        entries, crypto = classify_original(source, password)

        index_password = getpass.getpass(
            "New vault-index master password: "
        )
        confirmation = getpass.getpass(
            "Repeat vault-index master password: "
        )

        if not index_password or index_password != confirmation:
            raise RuntimeError("Index passwords do not match.")

        if index_password == password:
            raise RuntimeError(
                "Index password must differ from the original password."
            )

        confirmation = None

        os.mkdir(output_dir, 0o700)
        directory_created = True
        os.chmod(output_dir, 0o700)

        for number, (path, entry_uuid, title) in enumerate(
            entries, start=1
        ):
            stage = f"copy and isolation {number}"

            filename = secrets.token_hex(16) + ".kdbx"
            destination = os.path.join(output_dir, filename)

            entry_password = secrets.token_urlsafe(32)

            create_copy(source, destination)
            created_files.append(destination)

            isolate_entry(
                destination,
                password,
                path,
                entry_uuid,
                crypto,
            )

            stage = f"password change {number}"

            change_database_password(
                destination,
                password,
                entry_password,
            )

            stage = f"individual validation {number}"

            verify_individual(
                destination,
                entry_password,
                entry_uuid,
                crypto,
            )

            records.append({
                "filename": filename,
                "title": title,
                "password": entry_password,
            })

            print(f"Entry {number}: isolated, secured and validated.")

        stage = "index creation"

        index_path = os.path.join(output_dir, "vault-index.kdbx")

        create_copy(source, index_path)
        created_files.append(index_path)

        clear_index_database(index_path, password)

        change_database_password(
            index_path,
            password,
            index_password,
        )

        stage = "index population"

        for record in records:
            add_index_entry(
                index_path,
                index_password,
                record["title"],
                record["filename"],
                record["password"],
            )

        stage = "index validation"

        validate_index(index_path, index_password, records)

        print()
        print(f"Successfully processed: {len(records)}")
        print("Individual databases validated.")
        print("Vault index created and validated.")
        print("Original database was not modified.")

        success = True
        return 0

    except (pexpect.TIMEOUT, pexpect.EOF):
        print(f"Interaction failed during {stage}.")
        return 1

    except RuntimeError as error:
        print(f"Processing failed during {stage}: {error}")
        return 1

    except Exception as error:
        print(f"Processing failed during {stage}: {type(error).__name__}.")
        return 1

    finally:
        password = None
        index_password = None

        for record in records:
            record["password"] = None

        records.clear()

        if created_files and not success:
            for filename in created_files:
                try:
                    os.unlink(filename)
                except OSError:
                    pass

        if directory_created:
            try:
                os.rmdir(output_dir)
            except OSError:
                pass


if __name__ == "__main__":
    sys.exit(main())
