#! /usr/bin/env python3

import requests
from bs4 import BeautifulSoup

import myemail

import time

from selenium import webdriver


with open("/home/luyiming/dotfiles/bin/qgx_notes.txt", "r") as f:
    t = f.read().strip()
    if t != '':
        previousElements = int(t)


driver = webdriver.PhantomJS()
driver.get(url)
soup = BeautifulSoup(driver.page_source, "html.parser")


driver.quit()

data = {'pageNumber' : 0, 'pageSize' : 1}
r = requests.post('http://qinggongxiao.nju.edu.cn/cys/course/getCourses', data = data)
results = r.json()
increase = results.get('totalElements') - previousElements
if increase:
    if increase > 1:
        data['pageSize'] = increase
        r = requests.post('http://qinggongxiao.nju.edu.cn/cys/course/getCourses', data = data)
        results = r.json()
    for i in range(results.get('size')):
        result = results.get('content')[i]
        id = content.get('id')


def do_notify(note):
    subject = '青共校通知 - ' + note.name
    content = note.name + '\n'
    soup = BeautifulSoup(requests.get(note.href).text, "html.parser")
    content = content + soup.find("textarea").text
    e = myemail.Email(subject, content)
    e.send()


notes = []
hrefs = []

last_number = 0

with open("/home/luyiming/dotfiles/bin/notes.txt", "r") as f:
    t = f.read().strip()
    if t != '':
        last_number = int(t)

url = "http://qinggongxiao.nju.edu.cn/cys/index.html#/home"

soup = BeautifulSoup(requests.get(url).text, "html.parser")

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
            with open("/home/luyiming/dotfiles/bin/notes.txt", "w") as f:
                f.write(str(note.number))
            with open("/home/luyiming/dotfiles/bin/log.txt", "a+") as f:
                f.write("notify at " + time.ctime(time.time()) + '\n')
        notes.append(note)
