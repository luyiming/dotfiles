install:
	@ln -si $(CURDIR)/bash/bash_history ~/.bash_history
	@ln -si $(CURDIR)/bash/bashrc ~/.bashrc
	@ln -si $(CURDIR)/tmux/tmux.conf ~/.tmux.conf
	@ln -si $(CURDIR)/vim/vimrc ~/.vimrc
	@ln -si $(CURDIR)/zsh/zshrc ~/.zshrc
	@ln -si $(CURDIR)/zsh/zsh_history ~/.zsh_history
	@ln -si $(CURDIR)/git/gitconfig ~/.gitconfig

clean:
	@rm -i  ~/.bash_history
	@rm -i  ~/.bashrc
	@rm -i  ~/.tmux.conf
	@rm -i  ~/.vimrc
	@rm -i  ~/.zshrc
	@rm -i  ~/.zsh_history
	@rm -i  ~/.gitconfig

