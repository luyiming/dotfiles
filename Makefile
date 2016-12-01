install:
	@ln -svi $(CURDIR)/bash/bash_history ~/.bash_history
	@ln -svi $(CURDIR)/bash/bashrc ~/.bashrc
	@ln -svi $(CURDIR)/tmux/tmux.conf ~/.tmux.conf
	@ln -svi $(CURDIR)/vim/vimrc ~/.vimrc
	@ln -svi $(CURDIR)/zsh/zshrc ~/.zshrc
	@ln -svi $(CURDIR)/zsh/zsh_history ~/.zsh_history
	@ln -svi $(CURDIR)/git/gitconfig ~/.gitconfig
	@ln -svi $(CURDIR)/shadowsocks/config.json ~/config.json
	@cp -rvi $(CURDIR)/vim/colors ~/.vim/


clean:
	@rm -i  ~/.bash_history
	@rm -i  ~/.bashrc
	@rm -i  ~/.tmux.conf
	@rm -i  ~/.vimrc
	@rm -i  ~/.zshrc
	@rm -i  ~/.zsh_history
	@rm -i  ~/.gitconfig
	@rm -i  ~/config.json
