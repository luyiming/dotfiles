sudo apt-get update
sudo apt-get upgrade

# add user luyiming
useradd -m luyiming
passwd luyiming
# 给用户添加 sudo 命令的使用权限
echo -e "\nluyiming ALL=(ALL) ALL\n" >> /etc/sudoers

# 解决 sudo 无法解析 hosts 的问题
echo "aliyun" > /etc/hostname
cat /etc/hostname
echo -e "\n127.0.0.1 aliyun\n" >> /etc/hosts

# oh-my-zsh
sudo apt-get install zsh git curl
zsh
sh -c "$(curl -fsSL https://raw.github.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
git clone https://github.com/luyiming/dotfiles.githttps://github.com/luyiming/dotfiles.git
sudo chsh -s /usr/bin/zsh luyiming

# vim
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

# c/c++ dev environment
# automatically install g++,libc6-dev,linux-libc-dev,libstdc++6-4.1-dev... and so on
sudo apt-get install build-essential
sudo apt-get install cmake

# python
sudo apt-get install ipython ipython3
sudo pip install requests beautifulsoup4
sudo pip3 install requests beautifulsoup4
