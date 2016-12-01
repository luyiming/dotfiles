from email.header import Header
from email.mime.text import MIMEText
import smtplib

from_addr = "lym@notice.luyiming.win"
password = "lym9188888888"
to_addr = "151220066@smail.nju.edu.cn"
smtp_server = "smtpdm.aliyun.com"

msg = MIMEText('测试邮件内容', 'plain', 'utf-8')
msg['From'] = from_addr
msg['To'] = to_addr
msg['Subject'] = Header(u'测试邮件', 'utf-8').encode()

server = smtplib.SMTP(smtp_server, 25)
server.set_debuglevel(1)
server.login(from_addr, password)
server.sendmail(from_addr, [to_addr], msg.as_string())
server.quit()
