#!/usr/bin/env python3
import time

with open("/home/luyiming/dotfiles/bin/log.txt", "a+") as f:
    f.write(time.ctime(time.time()) + '\n')
