## 1. 问题

再拉取 apache/seatunnel 镜像时遇到如下异常：
```
localhost:seatunnel wy$ docker pull apache/seatunnel
Using default tag: latest
Error response from daemon: Get "https://registry-1.docker.io/v2/": net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)
```

## 2. 解决方案

首先测试网络连通性，使用 ping 或 curl 测试是否能访问 Docker Hub：
```
ping registry-1.docker.io
```
或者
```
curl -I https://registry-1.docker.io/v2/
```
可以看到无法访问 Docker Hub：
```
localhost:seatunnel wy$ ping registry-1.docker.io
PING registry-1.docker.io (45.114.11.238): 56 data bytes
Request timeout for icmp_seq 0
Request timeout for icmp_seq 1
Request timeout for icmp_seq 2
```
之前配置了阿里云的镜像加速服务，但是还是无法访问 Docker Hub，考虑镜像加速配置是否正确或者镜像加速地址是否有效。首先确认镜像加速配置是否正确：
```json
{
  "registry-mirrors": [
    "https://xxx.mirror.aliyuncs.com"
  ]
}
```
通过 `docker info` 命令在输出中查找 Registry Mirrors，确认镜像加速地址已正确加载。

下一步测试镜像加速地址是否有效。可以使用 curl 测试镜像加速地址是否可用：
```
localhost:~ wy$ curl -I https://xxx.mirror.aliyuncs.com
HTTP/2 403
date: Sat, 22 Feb 2025 11:15:47 GMT
content-type: text/plain
content-length: 189
```
如果返回 200 说明镜像加速地址可用；否则可能是镜像加速服务问题。从上述可以看到阿里云镜像加速服务有问题，尝试更换其他镜像加速地址，在这选择 `https://proxy.1panel.live` 加速地址：
```
localhost:~ wy$ curl -I https://proxy.1panel.live
HTTP/2 200
date: Sat, 22 Feb 2025 11:17:33 GMT
content-type: text/html
last-modified: Sat, 08 Feb 2025 16:44:46 GMT
vary: Accept-Encoding
strict-transport-security: max-age=31536000
alt-svc: h3=":443"; ma=86400
cf-cache-status: DYNAMIC
report-to: ...
```
返回 200 说明这次选择的加速地址有效。编辑 Docker 配置文件更换加速地址：
```
{
  ..
  "registry-mirrors": [
    "https://proxy.1panel.live"
  ]
}
```
> 记得重启 Docker 服务来生效新的配置

再次拉取镜像判断是否有效：
```
localhost:~ wy$ docker pull apache/seatunnel
Using default tag: latest
latest: Pulling from apache/seatunnel
001c52e26ad5: Pull complete
d9d4b9b6e964: Pull complete
2068746827ec: Pull complete
9daef329d350: Pull complete
d85151f15b66: Pull complete
52a8c426d30b: Pull complete
8754a66e0050: Pull complete
f6db9149f114: Pull complete
9ea33dc73841: Pull complete
4f4fb700ef54: Pull complete
Digest: sha256:21cb55d1d61dc154f3ae23e3d55035534c792115a38daf25fdad8fa4bcc09e0e
Status: Downloaded newer image for apache/seatunnel:latest
docker.io/apache/seatunnel:latest
(base) localhost:~ wy$
```
从上面可以看到更换加速地址解决问题。
