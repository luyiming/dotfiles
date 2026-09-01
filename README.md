Installation
------------
Your first step is to clone this repository:

```
git clone https://github.com/luyiming/dotfiles.git ~/.dotfiles
```

### Manual Installation
Create symbolic links for the configurations you want to use, e.g.:

```
ln -s ~/.dotfiles/tmux/.tmux.conf ~/.tmux.conf
```

### Automatic Installation
Then simply use `make` to install the dotfiles you want to use:

```
cd ~/.dotfiles
make tmux
```

### Command-line Tools

`manage_tools.py` installs or updates a selected set of command-line tools on
Ubuntu 22.04 or newer and Debian 12 or newer, on x86_64 systems. It requires
Python 3.8 or newer.

Expose the command in `~/.local/bin` once:

```sh
just install-tools-cli
```

Then run it from anywhere:

```sh
dottools --list
dottools ripgrep fd fzf neovim
dottools --interactive
dottools --check --all
```

With no arguments, an interactive terminal opens the selector. In a
non-interactive environment, tool names or `--all` are required. `--check` is
read-only and reports missing tools or available updates.

Tools configured with a continuous APT repository are installed only once;
APT owns their later updates. Rust is also installed only once and is then
managed manually with `rustup`. Other selected tools are updated to their
latest stable releases. Set `GITHUB_TOKEN` when needed to avoid unauthenticated
GitHub API rate limits.
