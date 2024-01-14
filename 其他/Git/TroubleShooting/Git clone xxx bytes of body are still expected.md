## 1. 问题

在使用 Git 克隆代码时出现如下问题：
```
localhost:OpenSource wy$ git clone https://github.com/sjf0115/FlagData.git
Cloning into 'FlagData'...
remote: Enumerating objects: 172, done.
remote: Counting objects: 100% (59/59), done.
remote: Compressing objects: 100% (47/47), done.
error: RPC failed; curl 18 HTTP/2 stream 5 was resetB/s
error: 7575 bytes of body are still expected
fetch-pack: unexpected disconnect while reading sideband packet
fatal: early EOF
fatal: fetch-pack: invalid index-pack output
```

## 2. 解决方案

如果 Git 项目太大，拉代码的时候可能会出现这个错误。可以先使用 `git config --list` 命令查看缓冲区 `https.postbuffer` 参数的大小。如果太小，可以通过使用如下方法增大缓冲区：
```
git config --global https.postBuffer 3097152000
```
再次使用 Git 克隆代码：
```
localhost:OpenSource wy$ git clone https://github.com/sjf0115/FlagData.git
Cloning into 'FlagData'...
remote: Enumerating objects: 172, done.
remote: Counting objects: 100% (59/59), done.
remote: Compressing objects: 100% (47/47), done.
remote: Total 172 (delta 21), reused 18 (delta 12), pack-reused 113
Receiving objects: 100% (172/172), 18.42 MiB | 150.00 KiB/s, done.
Resolving deltas: 100% (23/23), done.
```
