### 1. 响应内容

```Python
import requests

# 请求
r = requests.get('https://api.github.com/events')
print r.text
# [{"id":"6938738042","type":"CreateEvent","actor":{"id":34232897,"login" ...
```
请求会自动解码来自服务器的内容。大多数`unicode`字符集都是无缝解码的。

当你发出请求时，`Requests`会根据HTTP头(header)对响应(response)进行编码猜测。当你访问`r.text`时，将使用由`Requests`猜测的文本编码。可以使用`r.encoding`属性找出`Requests`正在使用编码的方式，并对其进行更改：
```Python
# 请求编码方式
print r.encoding  # utf-8
# 更改编码方式
r.encoding = 'ISO-8859-1'
print r.encoding  # ISO-8859-1
```

如果你更改编码，`Requests`将在你调用`r.text`时使用`r.encoding`的新值。你可能想在任何情形下，都可以使用特殊逻辑来计算出文本内容的编码方式。例如，`HTML`和`XML`能够在`body`中指定编码方式。在这种情况下，你应该使用`r.content`来查找编码，然后设置`r.encoding`。这会让在正确的编码方式下使用`r.text`。

如果你需要，`Requests`也可以使用自定义编码方式。如果你已经创建了自己的编码并将其注册到编解码器模块，你可以简单地使用编解码器名称作为`r.encoding`的值，`Requests`将为你处理解码。


















原文: http://docs.python-requests.org/en/latest/user/quickstart/#response-content
