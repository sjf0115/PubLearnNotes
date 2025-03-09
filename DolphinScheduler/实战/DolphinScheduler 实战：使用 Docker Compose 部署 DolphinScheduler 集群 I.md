
`.env` 配置文件：
```
HUB=apache
TAG=3.1.9

TZ=Asia/Shanghai
DATABASE=postgresql
SPRING_DATASOURCE_URL=jdbc:postgresql://dolphinscheduler-postgresql:5432/dolphinscheduler
REGISTRY_ZOOKEEPER_CONNECT_STRING=dolphinscheduler-zookeeper:2181
```


```yaml
version: "3.8"

services:
  dolphinscheduler-postgresql:
    image: bitnami/postgresql:11.11.0
    container_name: postgresql
    ports:
      - "5432:5432"
    profiles: ["all", "schema"]
    environment:
      POSTGRESQL_USERNAME: root
      POSTGRESQL_PASSWORD: root
      POSTGRESQL_DATABASE: dolphinscheduler
    volumes:
      - dolphinscheduler-postgresql:/bitnami/postgresql
    healthcheck:
      test: ["CMD", "bash", "-c", "cat < /dev/null > /dev/tcp/127.0.0.1/5432"]
      interval: 5s
      timeout: 60s
      retries: 120
    networks:
      - pub-network

  dolphinscheduler-zookeeper:
    image: bitnami/zookeeper:3.6.2
    container_name: zookeeper
    profiles: ["all"]
    environment:
      ALLOW_ANONYMOUS_LOGIN: "yes"
      ZOO_4LW_COMMANDS_WHITELIST: srvr,ruok,wchs,cons
    volumes:
      - dolphinscheduler-zookeeper:/bitnami/zookeeper
    healthcheck:
      test: ["CMD", "bash", "-c", "cat < /dev/null > /dev/tcp/127.0.0.1/2181"]
      interval: 5s
      timeout: 60s
      retries: 120
    networks:
      - pub-network

  dolphinscheduler-schema-initializer:
    image: apache/dolphinscheduler-tools:3.1.9
    container_name: schema-initializer
    env_file: .env
    profiles: ["schema"]
    command: [ tools/bin/upgrade-schema.sh ]
    depends_on:
      dolphinscheduler-postgresql:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - pub-network

  dolphinscheduler-api:
    image: apache/dolphinscheduler-api:3.1.9
    container_name: api
    ports:
      - "12345:12345"
      - "25333:25333"
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:12345/dolphinscheduler/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - pub-network

  dolphinscheduler-alert:
    image: apache/dolphinscheduler-alert-server:3.1.9
    container_name: alert
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:50053/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
    networks:
      - pub-network

  dolphinscheduler-master:
    image: apache/dolphinscheduler-master:3.1.9
    container_name: master
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:5679/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
    networks:
      - pub-network

  dolphinscheduler-worker:
    image: apache/dolphinscheduler-worker:3.1.9
    container_name: worker
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:1235/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-worker-data:/tmp/dolphinscheduler
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - pub-network

volumes:
  dolphinscheduler-postgresql:
  dolphinscheduler-zookeeper:
  dolphinscheduler-worker-data:
  dolphinscheduler-logs:
  dolphinscheduler-shared-local:
  dolphinscheduler-resource-local:

networks:  # 网络
  pub-network:
      external: true
```



第一次需要初始化，需要指定 `profile` 为 `schema`:
```bash
localhost:dolphinscheduler wy$ docker-compose --profile schema up -d
[+] Running 22/22
 ✔ dolphinscheduler-schema-initializer Pulled   23.4s
 ✔ dolphinscheduler-postgresql Pulled  36.5s
...
[+] Running 6/6
 ✔ Volume "dolphinscheduler_dolphinscheduler-shared-local"    Created  0.0s
 ✔ Volume "dolphinscheduler_dolphinscheduler-resource-local"  Created  0.0s
 ✔ Volume "dolphinscheduler_dolphinscheduler-postgresql"      Created  0.0s
 ✔ Volume "dolphinscheduler_dolphinscheduler-logs"            Created  0.0s
 ✔ Container postgresql                                       Healthy  0.9s
 ✔ Container schema-initializer                               Started  0.3s
```
启动 `dolphinscheduler` 所有服务，指定 `profile` 为 `all`：
```bash
localhost:dolphinscheduler wy$ docker-compose --profile all up -d
[+] Running 8/8
 ✔ Volume "dolphinscheduler_dolphinscheduler-worker-data"  Created   0.0s
 ✔ Volume "dolphinscheduler_dolphinscheduler-zookeeper"    Created   0.0s
 ✔ Container postgresql                                    Running   0.0s
 ✔ Container zookeeper                                     Healthy   1.3s
 ✔ Container alert                                         Started   1.3s
 ✔ Container worker                                        Started   0.3s
 ✔ Container api                                           Started   0.3s
 ✔ Container master                                        Started   0.3s
```

登录系统
不管你是用那种方式启动的服务，只要服务启动后，你都可以通过 http://localhost:12345/dolphinscheduler/ui 访问 DolphinScheduler。访问上述链接后会跳转到登陆页面，DolphinScheduler 默认的用户和密码分别为 admin 和 dolphinscheduler123。 想要了解更多操作请参考用户手册快速上手。



## 2. 沿用已有的 PostgreSQL 和 ZooKeeper 服务

使用上面的启动服务会新启动数据库以及 ZooKeeper 服务。如果你已经有在运行中的数据库或者 ZooKeeper 且不想启动新的服务，可以使用这个方式在沿用已有的 PostgreSQL 和 ZooKeeper 服务前提下启动 DolphinScheduler 各服务。

### 2.1 初始化数据

启动一个名为 `dolphinscheduler-tools` 的工具容器，执行数据库 `schema` 初始化操作：
```bash
docker run -d --name dolphinscheduler-tools \
    -e DATABASE="postgresql" \
    -e SPRING_DATASOURCE_URL="jdbc:postgresql://docker_postgres:5432/dolphinscheduler" \
    -e SPRING_DATASOURCE_USERNAME="postgres" \
    -e SPRING_DATASOURCE_PASSWORD="root" \
    -e SPRING_JACKSON_TIME_ZONE="UTC" \
    --net pub-network \
    apache/dolphinscheduler-tools:3.1.9 tools/bin/upgrade-schema.sh
```
需要注意的是运行上述命令之前先确保指定的数据库 `dolphinscheduler` 已经存在。如果没有的话，可以使用如下命令创建：
```sql
CREATE DATABASE dolphinscheduler;
```

核心配置说明：
配置容器内应用的环境变量，关键参数如下：
- `DATABASE`: 在这指定为 "postgresql"，声明数据库类型为 `PostgreSQL`。`DolphinScheduler` 支持 `PostgreSQL` 和 `MySQL` 两种数据库。
- `SPRING_DATASOURCE_URL`: 数据库连接 URL。
- `SPRING_DATASOURCE_USERNAME`: 数据库用户名。
- `SPRING_DATASOURCE_PASSWORD`: 数据库密码。
- `SPRING_JACKSON_TIME_ZONE`: 设置 Jackson 序列化/反序列化的时区为 UTC，确保时间处理一致性。
- `--net`: 加入的 Docker 自定义网络。

> 该容器的使用场景：
> - 版本升级: 当升级 DolphinScheduler 时，若新版本要求数据库结构变更，需通过此命令迁移 schema。
> - 初始化数据库: 首次安装时可能需要初始化数据库（具体依赖文档说明）。

运行之后查看日志初始化是否成功：
```bash
localhost:~ wy$ docker logs dolphinscheduler-tools
....
2025-03-05 06:56:38.853  INFO 8 --- [           main] .d.UpgradeDolphinScheduler$UpgradeRunner : init DolphinScheduler finished
2025-03-05 06:56:38.859  INFO 8 --- [ionShutdownHook] com.zaxxer.hikari.HikariDataSource       : DolphinScheduler - Shutdown initiated...
2025-03-05 06:56:38.864  INFO 8 --- [ionShutdownHook] com.zaxxer.hikari.HikariDataSource       : DolphinScheduler - Shutdown completed.
```
可以看到 `init DolphinScheduler finished` 信息表示初始化完成。也可以登录到 PostgreSQL 查看数据库下是否创建了对应的表：
```
List of relations
Schema |                     Name                      |   Type   |  Owner
--------+-----------------------------------------------+----------+----------
public | qrtz_blob_triggers                            | table    | postgres
public | qrtz_calendars                                | table    | postgres
public | qrtz_cron_triggers                            | table    | postgres
public | qrtz_fired_triggers                           | table    | postgres
public | qrtz_job_details                              | table    | postgres
public | qrtz_locks                                    | table    | postgres
public | qrtz_paused_trigger_grps                      | table    | postgres
public | qrtz_scheduler_state                          | table    | postgres
public | qrtz_simple_triggers                          | table    | postgres
public | qrtz_simprop_triggers                         | table    | postgres
public | qrtz_triggers                                 | table    | postgres
public | t_ds_access_token                             | table    | postgres
public | t_ds_access_token_id_sequence                 | sequence | postgres
...
```

### 2.2 启动 DolphinScheduler 服务

启动 `DolphinScheduler` 服务之前请确保依赖的 `PostgreSQL` 和 `ZooKeeper` 服务已经启动。下面就可以启动 DolphinScheduler 服务。

#### 2.2.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `dolphinscheduler` 的项目：
```shell
smartsi@localhost docker % mkdir dolphinscheduler
smartsi@localhost docker % cd dolphinscheduler
```

#### 2.2.2 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个`docker-compose.yml`文件，从官方 []()下载配置文件，去掉 PostgreSQL 和 ZooKeeper 服务部分，其它按照自己的需求调整即可。在这我们的配置如下所示：
```yaml
services:
  dolphinscheduler-master:
    image: apache/dolphinscheduler-master:3.1.9
    container_name: dolphinscheduler-master
    environment:
      - DATABASE=postgresql
      - SPRING_DATASOURCE_URL=jdbc:postgresql://docker_postgres:5432/dolphinscheduler
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=root
      - REGISTRY_ZOOKEEPER_CONNECT_STRING=docker_zk1:2181
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
    networks:
      - pub-network

  dolphinscheduler-worker:
    image: apache/dolphinscheduler-worker:3.1.9
    container_name: dolphinscheduler-worker
    environment:
      - DATABASE=postgresql
      - SPRING_DATASOURCE_URL=jdbc:postgresql://docker_postgres:5432/dolphinscheduler
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=root
      - REGISTRY_ZOOKEEPER_CONNECT_STRING=docker_zk1:2181
    volumes:
      - dolphinscheduler-worker-data:/tmp/dolphinscheduler
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - pub-network

  dolphinscheduler-api:
    image: apache/dolphinscheduler-api:3.1.9
    container_name: dolphinscheduler-api
    ports:
      - "12345:12345"
      - "25333:25333"
    environment:
      - DATABASE=postgresql
      - SPRING_DATASOURCE_URL=jdbc:postgresql://docker_postgres:5432/dolphinscheduler
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=root
      - REGISTRY_ZOOKEEPER_CONNECT_STRING=docker_zk1:2181
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - pub-network

  dolphinscheduler-alert:
    image: apache/dolphinscheduler-alert-server:3.1.9
    container_name: dolphinscheduler-alert
    environment:
      - DATABASE=postgresql
      - SPRING_DATASOURCE_URL=jdbc:postgresql://docker_postgres:5432/dolphinscheduler
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=root
      - REGISTRY_ZOOKEEPER_CONNECT_STRING=docker_zk1:2181
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
    networks:
      - pub-network

volumes:
  dolphinscheduler-worker-data:
  dolphinscheduler-logs:
  dolphinscheduler-shared-local:
  dolphinscheduler-resource-local:

networks:  # 网络
  pub-network:
      external: true
```

### 服务定义（Services）
`services` 是 `docker-compose.yml` 的核心部分，定义了多个容器服务。每个服务对应一个 DolphinScheduler 组件。

---

### **2. `dolphinscheduler-master` 服务**
#### **配置解析**
- **`image: apache/dolphinscheduler-master:3.1.9`**  
  使用 `apache/dolphinscheduler-master` 镜像，版本为 `3.1.9`。

- **`container_name: dolphinscheduler-master`**  
  指定容器名称为 `dolphinscheduler-master`，便于管理和识别。

- **`environment`**  
  设置环境变量，配置 Master 服务的运行参数：
  - **`DATABASE=postgresql`**  
    指定数据库类型为 PostgreSQL。
  - **`SPRING_DATASOURCE_URL=jdbc:postgresql://docker_postgres:5432/dolphinscheduler`**  
    数据库连接 URL，指向 PostgreSQL 服务（`docker_postgres` 是 PostgreSQL 容器名称）。
  - **`SPRING_DATASOURCE_USERNAME=postgres`**  
    数据库用户名。
  - **`SPRING_DATASOURCE_PASSWORD=root`**  
    数据库密码。
  - **`REGISTRY_ZOOKEEPER_CONNECT_STRING=docker_zk1:2181`**  
    Zookeeper 连接地址，用于服务注册与发现。

- **`healthcheck`**  
  定义健康检查机制：
  - **`test: [ "CMD", "curl", "http://localhost:5679/actuator/health" ]`**  
    通过 `curl` 检查 Master 服务的健康状态。
  - **`interval: 30s`**  
    每 30 秒检查一次。
  - **`timeout: 5s`**  
    每次检查超时时间为 5 秒。
  - **`retries: 3`**  
    失败重试 3 次。

- **`volumes`**  
  挂载数据卷：
  - **`dolphinscheduler-logs:/opt/dolphinscheduler/logs`**  
    将日志目录挂载到外部卷，便于持久化存储。
  - **`dolphinscheduler-shared-local:/opt/soft`**  
    挂载共享目录，用于存储临时文件或共享数据。

- **`networks`**  
  将服务连接到 `pub-network` 网络，确保容器间通信。

---

### **3. `dolphinscheduler-worker` 服务**
#### **配置解析**
- **`image: apache/dolphinscheduler-worker:3.1.9`**  
  使用 `apache/dolphinscheduler-worker` 镜像，版本为 `3.1.9`。

- **`container_name: dolphinscheduler-worker`**  
  指定容器名称为 `dolphinscheduler-worker`。

- **`environment`**  
  环境变量配置与 Master 服务类似，确保 Worker 能正确连接到数据库和 Zookeeper。

- **`healthcheck`**  
  健康检查配置：
  - **`test: [ "CMD", "curl", "http://localhost:1235/actuator/health" ]`**  
    检查 Worker 服务的健康状态。

- **`volumes`**  
  挂载数据卷：
  - **`dolphinscheduler-worker-data:/tmp/dolphinscheduler`**  
    挂载 Worker 数据目录。
  - **`dolphinscheduler-logs:/opt/dolphinscheduler/logs`**  
    挂载日志目录。
  - **`dolphinscheduler-shared-local:/opt/soft`**  
    挂载共享目录。
  - **`dolphinscheduler-resource-local:/dolphinscheduler`**  
    挂载资源目录，用于存储任务资源文件。

- **`networks`**  
  连接到 `pub-network` 网络。

---

### **4. `dolphinscheduler-api` 服务**
#### **配置解析**
- **`image: apache/dolphinscheduler-api:3.1.9`**  
  使用 `apache/dolphinscheduler-api` 镜像，版本为 `3.1.9`。

- **`container_name: dolphinscheduler-api`**  
  指定容器名称为 `dolphinscheduler-api`。

- **`ports`**  
  暴露端口：
  - **`"12345:12345"`**  
    将容器内的 12345 端口映射到宿主机的 12345 端口，用于 API 访问。
  - **`"25333:25333"`**  
    将容器内的 25333 端口映射到宿主机的 25333 端口，用于其他服务通信。

- **`environment`**  
  环境变量配置与 Master 和 Worker 服务类似。

- **`healthcheck`**  
  健康检查配置：
  - **`test: [ "CMD", "curl", "http://localhost:12345/dolphinscheduler/actuator/health" ]`**  
    检查 API 服务的健康状态。

- **`depends_on`**  
  定义服务依赖：
  - **`dolphinscheduler-zookeeper`**  
    确保 Zookeeper 服务健康后再启动 API 服务。

- **`volumes`**  
  挂载数据卷：
  - **`dolphinscheduler-logs:/opt/dolphinscheduler/logs`**  
    挂载日志目录。
  - **`dolphinscheduler-shared-local:/opt/soft`**  
    挂载共享目录。
  - **`dolphinscheduler-resource-local:/dolphinscheduler`**  
    挂载资源目录。

- **`networks`**  
  连接到 `pub-network` 网络。

---

### **5. `dolphinscheduler-alert` 服务**
#### **配置解析**
- **`image: apache/dolphinscheduler-alert-server:3.1.9`**  
  使用 `apache/dolphinscheduler-alert-server` 镜像，版本为 `3.1.9`。

- **`container_name: dolphinscheduler-alert`**  
  指定容器名称为 `dolphinscheduler-alert`。

- **`environment`**  
  环境变量配置与其他服务类似。

- **`healthcheck`**  
  健康检查配置：
  - **`test: [ "CMD", "curl", "http://localhost:50053/actuator/health" ]`**  
    检查 Alert 服务的健康状态。

- **`volumes`**  
  挂载数据卷：
  - **`dolphinscheduler-logs:/opt/dolphinscheduler/logs`**  
    挂载日志目录。

- **`networks`**  
  连接到 `pub-network` 网络。

---

### **6. `volumes` 配置**
定义数据卷，用于持久化存储：
- **`dolphinscheduler-worker-data`**  
  Worker 数据卷。
- **`dolphinscheduler-logs`**  
  日志数据卷。
- **`dolphinscheduler-shared-local`**  
  共享数据卷。
- **`dolphinscheduler-resource-local`**  
  资源数据卷。

---

### **7. `networks` 配置**
定义网络：
- **`pub-network`**  
  使用外部网络 `pub-network`，确保所有服务在同一网络中，能够互相通信。

---

### **总结**
该 `docker-compose.yml` 文件定义了 DolphinScheduler 的核心组件（Master、Worker、API、Alert），并通过环境变量、数据卷和网络配置，确保服务能够正确运行并持久化数据。每个服务的健康检查机制也保证了系统的稳定性。
