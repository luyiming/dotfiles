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
