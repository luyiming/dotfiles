#! /usr/bin/env python3
import requests
from bs4 import BeautifulSoup

import mail

import time

class Note(object):
    # 225 Nov 29 10:38【考试相关】关于12月全国大学英语四六级考试耳机试音及修理的通知 (897字节)0/108
    def __init__(self, number = 0, year = "", month = "", time = "", title = "", href = ""):
        self.number = number
        self.year = year
        self.month = month
        self.time = time
        self.title = title
        self.href = href
    def __str__(self):
        return "nr:%s %s %s %s %s %s" % (self.number, self.year, self.month, self.time, self.title, self.href)
    def __repr__(self):
        return "nr:%s %s %s %s %s %s" % (self.number, self.year, self.month, self.time, self.title, self.href)

def do_notify(note):
    subject = '博客通知 - ' + note.title
    content = note.href + '\n\n'
    soup = BeautifulSoup(requests.get(note.href).text, "html.parser")
    content = content + soup.find("textarea").text
    e = mail.Email()
    e.send_txt(subject, content)


notes = []
hrefs = []

last_number = 0

note_path= '/home/luyiming/dotfiles/bin/notify/.blog.note'
log_path = '/home/luyiming/dotfiles/bin/notify/notify.log'

with open(note_path, "r") as f:
    t = f.read().strip()
    if t != '':
        last_number = int(t)

bbs_url = "http://bbs.nju.edu.cn/blogdoc?userid=wang360&t=101type=-1"

soup = BeautifulSoup(requests.get(bbs_url).text, "html.parser")

for a in soup.find("table", width="600").find_all("a"):
    hrefs.append("http://bbs.nju.edu.cn/" + a["href"])

for line in soup.find("table", width="600").get_text().strip().split("\n"):
    line = line.split()
    if len(line) >= 5:
        number = int(line[0])
        title = line[3][5:] + " " + " ".join(line[4:-1])
        note = Note(number, line[1], line[2], line[3][:5], title, hrefs.pop(0))
        if number > last_number:
            do_notify(note)
            with open(note_path, "w") as f:
                f.write(str(note.number))
            with open(log_path, "a+") as f:
                f.write("blog notify at " + time.ctime(time.time()) + '\n')
        notes.append(note)
