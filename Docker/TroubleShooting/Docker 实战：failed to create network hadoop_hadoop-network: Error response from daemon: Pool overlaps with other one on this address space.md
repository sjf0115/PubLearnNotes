## 1. 问题

```shell
localhost:hadoop wy$ docker compose up -d
[+] Running 55/8
 ✔ nodemanager Pulled            126.9s
 ✔ namenode Pulled               127.6s
 ✔ resourcemanager Pulled        126.9s
 ✔ hiveserver2 Pulled            221.8s
 ✔ historyserver Pulled          127.5s
 ✔ hive-metastore-mysql Pulled   164.1s
 ✔ datanode Pulled               127.5s
 ✔ hive-metastore Pulled         221.8s
[+] Running 1/0
 ✘ Network hadoop_hadoop-network  Error     0.0s
failed to create network hadoop_hadoop-network: Error response from daemon: Pool overlaps with other one on this address space
```

## 2. 解决方案

### 错误原因分析

这个错误表明 Docker 在创建网络 `hadoop_hadoop-network` 时检测到 **IP 地址池与其他已有 Docker 网络重叠**。具体原因可能是：

1. **已有残留网络冲突**  
   - 之前运行过相同 Docker Compose 项目，其创建的网络未被清理，且使用了相同的子网配置。
   - 其他 Docker 网络占用了相同的子网地址范围（如 `172.x.x.x`）。

2. **显式子网配置冲突**  
   - 如果在 `docker-compose.yml` 中显式定义了网络子网（如 `subnet: 172.18.0.0/16`），而该子网已被其他网络占用。

---

### 解决方案

#### 方法 1: 清理残留网络
**适用于首次部署失败或确定旧网络可删除的情况**

1. **停止并删除旧容器和网络**  
   在项目目录下执行：
   ```bash
   docker compose down
   ```

2. **手动删除冲突网络**  
   如果残留网络未被 `docker compose down` 清理，手动删除：
   ```bash
   # 列出所有网络，找到名称类似 hadoop_hadoop-network 或冲突子网的网络
   docker network ls

   # 删除冲突网络
   docker network rm <冲突网络名称>
   ```

   ```json
   localhost:~ wy$ docker network inspect wordpress_db_wordpress-network
   [
       {
           "Name": "wordpress_db_wordpress-network",
           "Id": "df3f92386f56fd20fa8cd7536b74618be0d71b657405eb819d7be339f134abbf",
           "Created": "2024-05-11T14:28:33.347140356Z",
           "Scope": "local",
           "Driver": "bridge",
           "EnableIPv6": false,
           "IPAM": {
               "Driver": "default",
               "Options": null,
               "Config": [
                   {
                       "Subnet": "172.20.0.0/16",
                       "Gateway": "172.20.0.1"
                   }
               ]
           },
           "Internal": false,
           "Attachable": false,
           "Ingress": false,
           "ConfigFrom": {
               "Network": ""
           },
           "ConfigOnly": false,
           "Containers": {},
           "Options": {},
           "Labels": {
               "com.docker.compose.network": "wordpress-network",
               "com.docker.compose.project": "wordpress_db",
               "com.docker.compose.version": "2.26.1"
           }
       }
   ]
   ```



3. **重新启动集群**  
   ```bash
   docker compose up -d
   ```

 ```
 localhost:hadoop wy$ docker compose up -d
 [+] Running 8/8
  ✔ Container namenode              Running    0.0s
  ✔ Container hive-metastore-mysql  Started    0.3s
  ✔ Container resourcemanager       Started    0.4s
  ✔ Container datanode              Started    0.3s
  ✔ Container hive-metastore        Started    0.9s
  ✔ Container historyserver         Started    0.7s
  ✔ Container nodemanager           Started    0.5s
  ✔ Container hiveserver2           Started    0.6s
 ```


---

#### 方法 2: 修改子网配置
**适用于需要保留其他网络或需要固定子网的情况**

1. **编辑 `docker-compose.yml` 文件**  
   在 `networks` 配置部分显式指定一个不冲突的子网：
   ```yaml
   networks:
     hadoop-network:
       name: hadoop_hadoop-network
       driver: bridge
       ipam:
         config:
           - subnet: 172.20.0.0/16  # 修改为其他未使用的子网
   ```

2. **清理旧环境并重启**  
   ```bash
   docker compose down
   docker compose up -d
   ```

---

#### 方法 3: 完全重置 Docker 网络
**适用于不确定具体冲突来源且允许清理所有未使用网络的情况**

1. **删除所有未使用的 Docker 网络**  
   ```bash
   docker network prune
   ```

2. **重启集群**  
   ```bash
   docker compose up -d
   ```

---

### 验证步骤

1. **检查 Docker 网络列表**  
   ```bash
   docker network ls
   ```

2. **查看网络详情**  
   ```bash
   docker network inspect hadoop_hadoop-network
   ```
   确保 `Subnet` 字段的值不再与其他网络重叠。

---

### 附加建议

- **显式定义子网**  
  在 `docker-compose.yml` 中始终显式指定子网（如 `172.20.0.0/16`），避免 Docker 自动分配时发生冲突。

- **使用独立项目名称**  
  通过 `-p` 参数指定唯一项目名称，隔离不同环境：
  ```bash
  docker compose -p my-hadoop-cluster up -d
  ```

通过以上步骤，应能解决网络地址池重叠问题并成功启动 Hadoop 集群。
