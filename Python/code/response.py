# -*- coding: UTF-8 -*-

# 网络请求
import urllib
import chardet
import requests

# 请求
r = requests.get('https://api.github.com/events')
print r.text
# [{"id":"6938738042","type":"CreateEvent","actor":{"id":34232897,"login" ...

# 请求编码方式
print r.encoding  # utf-8
# 更改编码方式
r.encoding = 'ISO-8859-1'
print r.encoding  # ISO-8859-1


station_request = requests.get("http://www.jb51.net")
content_type = station_request.headers['content-type']
print content_type  # text/html; charset=utf-8
print station_request.encoding



# raw_data = urllib.urlopen('http://blog.csdn.net/sunnyyoona').read()
# print chardet.detect(raw_data)  # {'confidence': 0.99, 'encoding': 'utf-8'}
#

# 一等火车站
url = "https://baike.baidu.com/item/%E4%B8%80%E7%AD%89%E7%AB%99"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'}
r = requests.get(url, headers=headers)
print r.headers['Content-Type']  # text/html
# 猜测的编码方式
print r.encoding  # ISO-8859-1
print r.text  # 出现乱码

# 检测编码
raw_data = urllib.urlopen(url).read()
charset = chardet.detect(raw_data)  # {'confidence': 0.99, 'encoding': 'utf-8'}
encoding = charset['encoding']
# 更改编码方式
r.encoding = encoding
print r.text  # 未出现乱码