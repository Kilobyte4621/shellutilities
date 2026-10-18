test_passgen() {
    local script_dir
    script_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
    "$script_dir/../.venv/bin/python" "$script_dir/test_passgen.py" "$@"
}
