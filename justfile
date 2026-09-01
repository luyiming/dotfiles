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

# Expose the tool manager as dottools on PATH without replacing conflicts.
install-tools-cli:
    @source="$DOTFILES_REPO_ROOT/manage_tools.py"; \
        target="$HOME/.local/bin/dottools"; \
        if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then \
            printf 'Already linked: %s -> %s\n' "$target" "$source"; \
        elif [ -e "$target" ] || [ -L "$target" ]; then \
            printf 'Target already exists: %s\n' "$target" >&2; \
            exit 1; \
        else \
            mkdir -p "$(dirname "$target")"; \
            ln -s "$source" "$target"; \
            printf 'Linked: %s -> %s\n' "$target" "$source"; \
        fi
