#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.header import Header

class Email(object):
    def __init__(self):
        self._sender = '842688696@qq.com'
        self._receiver = '151220066@smail.nju.edu.cn'
        self._smtpserver = 'smtp.qq.com'
        self._smtpport = 465
        self._password = 'fihigitblzmwbdbd'

    def send_txt(self, subject, content):
        message = MIMEText(content, 'plain', 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = Header("自动提醒", 'utf-8')
        message['To'] =  Header("陆依鸣", 'utf-8')

        smtp = smtplib.SMTP_SSL()
        smtp.connect(self._smtpserver, self._smtpport)
        smtp.login(self._sender, self._password)
        smtp.sendmail(self._sender, [self._receiver], message.as_string())
        smtp.quit()

    def send_html(self, subject, content):
        msg = MIMEText(content)
        msg['Subject'] = subject
        me = '842688696@qq.com'
        you = '151220066@smail.nju.edu.cn'
        msg['From'] = me
        msg['To'] = you

        s = smtplib.SMTP('localhost')
        s.sendmail(me, [you], msg.as_string())
        s.quit()

e = Email()
e.send_html("test", "test")
