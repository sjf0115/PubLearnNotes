
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
    image: ${HUB}/dolphinscheduler-tools:${TAG}
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
    image: ${HUB}/dolphinscheduler-api:${TAG}
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
    image: ${HUB}/dolphinscheduler-alert-server:${TAG}
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
    image: ${HUB}/dolphinscheduler-master:${TAG}
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
    image: ${HUB}/dolphinscheduler-worker:${TAG}
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
