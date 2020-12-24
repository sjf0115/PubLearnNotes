


### 2. 解决办法

运行如下命令：
```
git fetch
git brance -r
```

### 3. 解析

#### 3.1 git fetch

默认情况下，git fetch 取回所有分支的更新。如果只想取回特定分支的更新，可以指定分支名:
```
git fetch <远程主机名> <分支名>
```
比如，取回origin主机的master分支。所取回的更新，在本地主机上要用”远程主机名/分支名”的形式读取。比如origin主机的master，就要用origin/master读取。





参考：https://blog.csdn.net/qq_25283709/article/details/78290277
