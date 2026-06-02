# Set up fzf key bindings
if command -q fzf
    set -gx FZF_DEFAULT_OPTS "--height=40% --layout=reverse --info=inline"
    fzf --fish | source
end
