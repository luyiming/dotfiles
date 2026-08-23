export DOTFILES_REPO_ROOT := justfile_directory()

[private]
default:
    @just --list

# Install the tmux configuration, backing up any existing configuration.
install-tmux:
    @"$DOTFILES_REPO_ROOT/scripts/install-link.sh" \
        "$DOTFILES_REPO_ROOT/tmux/.tmux.conf" \
        "$HOME/.tmux.conf"

# Install the shared agent instructions and skills.
install-agents:
    @"$DOTFILES_REPO_ROOT/scripts/install-link.sh" \
        "$DOTFILES_REPO_ROOT/agents/AGENTS.md" \
        "$HOME/.codex/AGENTS.md" \
        --discard-empty
    @"$DOTFILES_REPO_ROOT/scripts/install-link.sh" \
        "$DOTFILES_REPO_ROOT/agents/.agents/skills" \
        "$HOME/.agents/skills"
