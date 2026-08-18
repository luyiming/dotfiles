if status is-interactive
# Commands to run in interactive sessions can go here
end

set -gx LANG en_US.UTF-8

if command -q nvim
    set -gx EDITOR nvim
    set -gx VISUAL nvim
else
    set -gx EDITOR vim
    set -gx VISUAL vim
end

if set -q VSCODE_INJECTION; and test "$VSCODE_INJECTION" = "1"
    set -gx EDITOR "code --wait"
    set -gx VISUAL "code --wait"
end

set -gx PAGER less

# --redraw-on-quit was introduced in less 599.
if less --help 2>&1 | string match -qr -- '--redraw-on-quit'
    set -gx LESS "-FR --redraw-on-quit"
else
    set -gx LESS "-FR"
end

fish_config theme choose catppuccin-frappe --color-theme dark

bind up up-or-prefix-search
bind down down-or-prefix-search
bind ctrl-p up-or-prefix-search
bind ctrl-n down-or-prefix-search
