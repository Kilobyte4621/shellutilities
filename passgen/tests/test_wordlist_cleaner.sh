test_wordlist_cleaner() {
    python3 "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/test_wordlist_cleaner.py" "$@"
}
