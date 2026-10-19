
disktest() {
    local destructive=0 dev node type mnt answer confirm
    local failed=0 tested=0 rc
    local -a targets=() testfiles=()

    if [[ ${1:-} == "--destructive" ]]; then
        destructive=1
        shift
    fi

    if [[ $# -ne 1 ]]; then
        printf 'Uso: disktest [--destructive] /dev/sdX\n'
        return 2
    fi

    dev=$1

    if [[ ! -b "$dev" ]]; then
        printf 'Erro: dispositivo de bloco inválido: %s\n' "$dev"
        return 1
    fi

    dev=$(readlink -f -- "$dev") || return 1

    if ((destructive)); then
        if ! command -v f3probe >/dev/null 2>&1; then
            printf 'Falta o F3. Instale com: sudo apt install f3\n'
            return 1
        fi

        printf '\nMODO DESTRUTIVO: %s\n' "$dev"
        lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS "$dev"
        printf '\nATENÇÃO: este teste pode destruir os dados da mídia.\n'
        printf 'Confirme que selecionou o dispositivo correto.\n'
        printf 'Para continuar, digite exatamente "%s": ' "$dev"
        IFS= read -r confirm || return 1

        if [[ "$confirm" != "$dev" ]]; then
            printf 'Cancelado.\n'
            return 1
        fi

        # Não permite testar discos com sistemas de arquivos montados.
        while IFS= read -r node; do
            if findmnt -rn -S "$node" >/dev/null 2>&1; then
                printf 'Erro: %s está montado. Desmonte-o primeiro.\n' "$node"
                return 1
            fi

            if swapon --show=NAME --noheadings --raw 2>/dev/null |
                grep -Fxq -- "$node"; then
                printf 'Erro: %s está sendo usado como swap.\n' "$node"
                return 1
            fi
        done < <(lsblk -lnpo NAME "$dev")

        sudo f3probe --destructive "$dev"
        return $?
    fi

    if ! command -v f3write >/dev/null 2>&1 ||
       ! command -v f3read >/dev/null 2>&1; then
        printf 'Falta o F3. Instale com: sudo apt install f3\n'
        return 1
    fi

    printf '\nDispositivo selecionado:\n'
    lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS "$dev"
    printf '\nSerão testados os sistemas de arquivos montados neste dispositivo.\n'
    printf 'Nenhuma formatação será realizada.\n'
    printf 'Continuar? [s/N] '
    IFS= read -r answer || return 1
    [[ "$answer" =~ ^[sS]$ ]] || return 1

    while IFS= read -r -d '' node &&
          IFS= read -r -d '' type &&
          IFS= read -r -d '' mnt; do
        if [[ ( "$type" == "part" || "$type" == "disk" ) &&
              -n "$mnt" && -d "$mnt" ]]; then
            targets+=("$node"$'\t'"$mnt")
        fi
    done < <(
        lsblk -lnpo NAME,TYPE,MOUNTPOINT "$dev" |
        while read -r node type mnt; do
            printf '%s\0%s\0%s\0' "$node" "$type" "$mnt"
        done
    )

    if ((${#targets[@]} == 0)); then
        printf 'Nenhuma partição montada encontrada.\n'
        printf 'Monte a partição e execute novamente.\n'
        return 1
    fi

    for entry in "${targets[@]}"; do
        node=${entry%%$'\t'*}
        mnt=${entry#*$'\t'}

        printf '\n=== %s — %s ===\n' "$node" "$mnt"
        df -h -- "$mnt"

        shopt -s nullglob
        testfiles=("$mnt"/*.h2w)
        shopt -u nullglob

        if ((${#testfiles[@]})); then
            printf 'Erro: existem arquivos *.h2w em %s.\n' "$mnt"
            printf 'Não vou sobrescrevê-los. Resolva isso antes de continuar.\n'
            failed=1
            continue
        fi

        printf '\n--- Gravação ---\n'
        if f3write "$mnt"; then
            printf '\n--- Leitura e verificação ---\n'
            if f3read "$mnt"; then
                printf '\nRESULTADO: F3 sem erros reportados em %s\n' "$node"
            else
                rc=$?
                printf '\nFALHA: f3read retornou %d em %s\n' "$rc" "$node"
                failed=1
            fi
        else
            rc=$?
            printf '\nFALHA: f3write retornou %d em %s\n' "$rc" "$node"
            failed=1
        fi

        ((tested++))
    done

    printf '\n=== RESUMO ===\n'
    printf 'Sistemas de arquivos testados: %d\n' "$tested"
    printf 'Falhas ou testes não executados: %d\n' "$failed"

    if ((failed)); then
        return 1
    fi

    printf '\nOs arquivos *.h2w foram mantidos.\n'
    printf 'Remova-os somente após revisar os resultados.\n'
    return 0
}
