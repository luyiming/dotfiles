import urllib.request, urllib.parse, urllib.error
import http.cookiejar
cookie = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))
postdata = urllib.parse.urlencode({
    'username':'151220066', 
    'password':'320581199705290214',
    }).encode('utf-8')
login = 'http://p.nju.edu.cn/portal_io/login'
logout = 'http://p.nju.edu.cn/portal_io/logout'
req = urllib.request.Request(login, postdata)
response = opener.open(req)
page = response.read().decode('utf-8')
print(page)

