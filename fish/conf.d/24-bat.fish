# it might have different behavour for using bat in man pager
# https://github.com/sharkdp/bat/issues/1433

if command -q bat
    set -gx BAT_THEME_DARK "Catppuccin Frappe"

    switch "$(uname)"
    case "Darwin"
        set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"
    case "Linux"
        set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"
        # set -gx MANPAGER "bat -l man -p"
    case '*'
        set -gx MANPAGER "bat -l man -p"
    end
end
