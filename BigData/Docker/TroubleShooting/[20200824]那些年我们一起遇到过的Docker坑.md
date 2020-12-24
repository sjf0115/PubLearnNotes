### 1. The container name xxx is already in use

在使用如下命令启动 Zookeeper 容器：
```
docker run --name zookeeper-standalone --restart always -d zookeeper:3.5.8
```
报如下错误：
```
docker: Error response from daemon: Conflict. The container name "/zookeeper-standalone" is already in use by container "6862ee5bda9c23416abd941e8a5a0b573d38c6671a6f8e7b3acdff23707e4bc4". You have to remove (or rename) that container to be able to reuse that name.
See 'docker run --help'.
```
解决办法是使用如下命令显示全部容器，包括已停止的容器：
```
docker ps -a
```
我们可以看到确实有一个停止的容器：
```
wy:study wy$ docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS                       PORTS                NAMES
6862ee5bda9c        b7444097adb2        "/docker-entrypoint.…"   About an hour ago   Exited (143) 7 minutes ago                        zookeeper-standalone
```
使用如下命令删除容器即可：
```
docker rm 6862ee5bda9c
```
