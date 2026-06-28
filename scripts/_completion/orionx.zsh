#compdef orionx orionx-backup orionx-calendar orionx-contacts orionx-cookbook orionx-docs orionx-gallery orionx-mail orionx-mcp orionx-memory orionx-notes orionx-personal orionx-preset orionx-research orionx-sessions orionx-signature orionx-skills orionx-tasks orionx-theme orionx-webhook
# Zsh tab-completion for the orionx umbrella + sub-CLIs.
#
# Drop in any directory on $fpath, e.g.:
#     fpath=(/path/to/orionx-ui/scripts/_completion $fpath)
#     autoload -U compinit; compinit
#
# Then `orionx <tab>` completes subcommands; `orionx mail <tab>`
# completes mail subcommands; `orionx-mail <tab>` works the same.

_orionx_scripts_dir() {
    local self="${(%):-%x}"
    while [[ -L "$self" ]]; do self="$(readlink "$self")"; done
    cd "${self:h}/.." && pwd
}

typeset -gA _orionx_subs

_orionx_refresh() {
    _orionx_subs=()
    local dir="$(_orionx_scripts_dir)"
    local py="$dir/../venv/bin/python"
    [[ -x "$py" ]] || py="$(command -v python3)"
    local f sub help_out commands
    for f in "$dir"/orionx-*; do
        [[ -x "$f" ]] || continue
        case "$f" in
            *.bak|*.pyc|*.pre-*) continue ;;
        esac
        sub="${${f:t}#orionx-}"
        help_out=$("$py" "$f" --help 2>/dev/null) || continue
        commands=$(echo "$help_out" | grep -oE '\{[a-z0-9_,-]+\}' | head -1 \
            | tr -d '{}' | tr ',' ' ')
        _orionx_subs[$sub]="$commands"
    done
}

_orionx() {
    [[ ${#_orionx_subs} -eq 0 ]] && _orionx_refresh

    local cmd="${words[1]}"

    if [[ "$cmd" == "orionx" ]]; then
        if (( CURRENT == 2 )); then
            local -a subs=(${(k)_orionx_subs} help)
            _describe 'subcommand' subs
            return
        fi
        local sub="${words[2]}"
        if [[ "$sub" == "help" ]] && (( CURRENT == 3 )); then
            local -a subs=(${(k)_orionx_subs})
            _describe 'subcommand' subs
            return
        fi
        if (( CURRENT == 3 )); then
            local -a sc=(${(s/ /)_orionx_subs[$sub]})
            _describe 'command' sc
            return
        fi
        return
    fi

    # orionx-foo <tab>
    local sub="${cmd#orionx-}"
    if (( CURRENT == 2 )); then
        local -a sc=(${(s/ /)_orionx_subs[$sub]})
        _describe 'command' sc
        return
    fi
}

_orionx "$@"
