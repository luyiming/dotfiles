#!/bin/bash

REGULAR="\\033[0;39m"
YELLOW="\\033[1;33m"
GREEN="\\033[1;32m"
CYAN="\\033[1;36m"

backup() {
  target=$1
  if [ -e "$target" ]; then           # Does the config file already exist?
    if [ ! -L "$target" ]; then       # as a pure file? (not a symbolic link)
      mv "$target" "$target.backup"   # Then backup it
      echo "-----> Moved your old $target config file to $target.backup"
    fi
  fi
}

install() {
  target="$HOME/.`basename $1`"
  echo -e -n "${CYAN}install $target? (y/n) ${REGULAR}"
  read reply
  if [[ $reply == "y" ]]; then
      backup $target
      if [ ! -e "$target" ]; then
        echo "-----> Symlinking your new $target"
        ln -s "$PWD/$1" "$target"
      fi
  fi
}

install "zsh/zshrc"
install "zsh/dircolors"
install "git/gitconfig"
install "git/gitmessage"
install "vim/vimrc"
install "tmux/tmux.conf"

cp -r vim/colors ~/.vim/colors

echo -e "${GREEN}Carry on with git setup!"
