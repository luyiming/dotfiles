import urllib.request, urllib.parse, urllib.error
import http.cookiejar
import json
cookie = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))
postdata = urllib.parse.urlencode({
    'username':'151220066',
    'password':'Lu740320',
    }).encode('utf-8')
login = 'http://p.nju.edu.cn/portal_io/login'
logout = 'http://p.nju.edu.cn/portal_io/logout'
req = urllib.request.Request(login, postdata)
response = opener.open(req)
page = response.read().decode('utf-8')
print(json.dumps(json.loads(page), indent=4, ensure_ascii=False))
