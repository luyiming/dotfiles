.PHONY: all help tmux clean restore

# Backup directory
BACKUP_DIR := $(HOME)/.dotfiles_backup
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

# Default target
all: help

# Help target
help:
	@echo "Available targets:"
	@echo "  make tmux    - Install tmux configuration (backs up existing files)"
	@echo "  make clean   - Remove all installed dotfiles"
	@echo "  make restore - Restore backed up dotfiles"
	@echo "  make help    - Show this help message"

# Install tmux configuration
tmux:
	@echo "Installing tmux configuration..."
	@if [ -f $(HOME)/.tmux.conf ] && [ ! -L $(HOME)/.tmux.conf ]; then \
		mkdir -p $(BACKUP_DIR); \
		cp $(HOME)/.tmux.conf $(BACKUP_DIR)/.tmux.conf.$(TIMESTAMP); \
		echo "Backed up existing .tmux.conf to $(BACKUP_DIR)/.tmux.conf.$(TIMESTAMP)"; \
	fi
	@ln -sf $(HOME)/.dotfiles/tmux/.tmux.conf $(HOME)/.tmux.conf
	@echo "tmux configuration installed"

# Clean up installed dotfiles
clean:
	@echo "Removing installed dotfiles..."
	@if [ -L $(HOME)/.tmux.conf ]; then \
		rm -f $(HOME)/.tmux.conf; \
		echo "Removed symlink: .tmux.conf"; \
	else \
		echo "Warning: .tmux.conf is not a symlink, skipping"; \
	fi
	@echo "Dotfiles removed"

# Restore backed up dotfiles
restore:
	@echo "Available backups in $(BACKUP_DIR):"
	@if [ -d $(BACKUP_DIR) ]; then \
		ls -lht $(BACKUP_DIR) | grep -v '^total'; \
		echo ""; \
		echo "To restore, manually copy the desired backup file to its original location"; \
	else \
		echo "No backups found"; \
	fi
