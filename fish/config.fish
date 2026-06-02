if status is-interactive
# Commands to run in interactive sessions can go here
end

set -gx LANG en_US.UTF-8

set -gx EDITOR nvim
set -gx VISUAL nvim

set -gx LESS "-FR --redraw-on-quit"
set -gx PAGER less

fish_config theme choose catppuccin-frappe

bind up up-or-prefix-search
bind down down-or-prefix-search
bind ctrl-p up-or-prefix-search
bind ctrl-n down-or-prefix-search
