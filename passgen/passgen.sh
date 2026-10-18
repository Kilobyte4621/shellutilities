#passgen() {
#    local script_dir python_bin
#    script_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
#
#    if [[ -x "$script_dir/../.venv/bin/python" ]]; then
#        python_bin="$script_dir/../.venv/bin/python"
#    else
#        python_bin="python3"
#    fi
#
#    "$python_bin" "$script_dir/passgen.py" "$@"
#}

passgen() {
    local python_bin="$HOME/scripts/shellutilities/passgen/.venv/bin/python"
    "$python_bin" "$HOME/scripts/shellutilities/passgen/passgen.py" "$@"
}
#passgen -E 128

##passgen() {
#    "$HOME/scripts/shellutilities/passgen/.venv/bin/python" \
#        "$HOME/scripts/shellutilities/passgen/passgen.py" "$@"
#}

#passgen() {
#    local script_dir python_bin
#    script_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
#
#    if [[ -x "$script_dir/../.venv/bin/python" ]]; then
#        python_bin="$script_dir/../.venv/bin/python"
#    else
#        python_bin="python3"
#    fi
#
#    "$python_bin" "$script_dir/passgen.py" "$@"
#}
