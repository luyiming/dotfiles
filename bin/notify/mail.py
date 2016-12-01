import smtplib
from email.mime.text import MIMEText
from email.header import Header

class Email(object):
    def __init__(self):
        self.sender = 'lym@notice.luyiming.win'
        self.receiver = '151220066@smail.nju.edu.cn'
        self.smtpserver = 'smtpdm.aliyun.com'
        self.smtpport = 465
        self.password = 'lym9188888888'

    def send_txt(self, subject, content):
        message = MIMEText(content, 'plain', 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = Header("自动提醒<lym@notice.luyiming.win>", 'utf-8')
        message['To'] =  Header("151220066@smail.nju.edu.cn", 'utf-8')
        _send(message)

    def send_html(self, subject, content):
        message = MIMEText(content, 'html', 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = Header("自动提醒<lym@notice.luyiming.win>", 'utf-8')
        message['To'] =  Header("151220066@smail.nju.edu.cn", 'utf-8')
        _send(message)

    def _send(self, message):
        smtp = smtplib.SMTP_SSL()
        smtp.connect(self.smtpserver, self.smtpport)
        smtp.login(self.sender, self.password)
        smtp.sendmail(self.sender, [self.receiver], message.as_string())
        smtp.quit()
