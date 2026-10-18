test_wordlist_cleaner() {
    local script_dir python_bin
    script_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

    if [[ -x "$script_dir/../.venv/bin/python" ]]; then
        python_bin="$script_dir/../.venv/bin/python"
    else
        python_bin="python3"
    fi

    "$python_bin" "$script_dir/test_wordlist_cleaner.py" "$@"
}
