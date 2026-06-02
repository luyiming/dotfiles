if not command -q eza
    return
end

# Use eza as a modern replacement for ls
alias ls="eza"

# Long listing view
alias l="eza -l --smart-group --time-style long-iso"

# Long listing view including hidden files
alias la="eza -la --smart-group --time-style long-iso"

# Detailed listing with hidden files and git status and a header
alias ll="eza -lah --smart-group --git --time-style long-iso"

# List only directories (excluding dotdirs) as a long list
alias ld="eza -lD --smart-group --time-style long-iso"

# List only directories (including dotdirs) as a long list
alias ldd="eza -laD --smart-group --time-style long-iso"

# Long listing of files only, sorted by size (largest last)
alias lS="eza -la --only-files --smart-group --time-style long-iso -ssize"

# Long listing sorted by modification time (newest last)
alias lT="eza -la --smart-group --time-style long-iso -snewest"

# Tree view (expand and edit depth as needed)
abbr -a lt --set-cursor "eza -la --smart-group --git --time-style long-iso --tree -L %"

# Directory-only tree view
abbr -a ltd --set-cursor "eza -laD --smart-group --git --time-style long-iso --tree -L %"
