install:
	@ln -svi $(CURDIR)/bash/bashrc ~/.bashrc
	@ln -svi $(CURDIR)/tmux/tmux.conf ~/.tmux.conf
	@ln -svi $(CURDIR)/vim/vimrc ~/.vimrc
	@ln -svi $(CURDIR)/zsh/zshrc ~/.zshrc
	@ln -svi $(CURDIR)/zsh/dircolors ~/.dircolors
	@ln -svi $(CURDIR)/git/gitconfig ~/.gitconfig
	@ln -svi $(CURDIR)/shadowsocks/config.json ~/config.json
	@cp -rvi $(CURDIR)/vim/colors ~/.vim/


clean:
	@rm -i  ~/.bashrc
	@rm -i  ~/.tmux.conf
	@rm -i  ~/.vimrc
	@rm -i  ~/.zshrc
	@rm -i  ~/.dircolors
	@rm -i  ~/.gitconfig
	@rm -i  ~/config.json
