
## 1. 问题

使用如下 docker-compose.yml 配置文件部署 Hive 服务：
```yaml
services:
  postgres:
    image: postgres:15.7
    restart: unless-stopped
    container_name: postgres
    hostname: postgres
    environment:
      POSTGRES_DB: 'hive_metastore'
      POSTGRES_USER: 'admin'
      POSTGRES_PASSWORD: 'admin'
    ports:
      - '5432:5432'
    volumes:
      - pg:/var/lib/postgresql
    networks:
      - pub-network

  metastore:
    image: apache/hive:3.1.3
    depends_on:
      - postgres
    restart: unless-stopped
    container_name: metastore
    hostname: metastore
    environment:
      DB_DRIVER: postgres
      SERVICE_NAME: 'metastore'
      SERVICE_OPTS: '-Xmx1G -Djavax.jdo.option.ConnectionDriverName=org.postgresql.Driver
                     -Djavax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/hive_metastore
                     -Djavax.jdo.option.ConnectionUserName=admin
                     -Djavax.jdo.option.ConnectionPassword=admin'
    ports:
        - '9083:9083'
    volumes:
        - warehouse:/opt/hive/data/warehouse
        - ./lib/postgresql-42.5.6.jar:/opt/hive/lib/postgres.jar
        - ./hadoop-conf:/opt/hive/conf
    networks:
      - pub-network

  hiveserver2:
    image: apache/hive:3.1.3
    depends_on:
      - metastore
    restart: unless-stopped
    container_name: hiveserver2
    environment:
      HIVE_SERVER2_THRIFT_PORT: 10000
      SERVICE_OPTS: '-Xmx1G -Dhive.metastore.uris=thrift://metastore:9083'
      IS_RESUME: 'true'
      SERVICE_NAME: 'hiveserver2'
    ports:
      - '10000:10000'
      - '10002:10002'
    volumes:
      - warehouse:/opt/hive/data/warehouse
      - ./hadoop-conf:/opt/hive/conf
    networks:
      - pub-network

volumes:
  pg:
  warehouse:

networks:
  pub-network:
    external: true
```
`hadoop-conf` 添加了 `core-site.xml`、`hdfs-site.xml`、`yarn-site.xml` 以及 `hive-site.xml` 几个配置文件。

部署完成之后执行 `docker exec -it hiveserver2 beeline -u 'jdbc:hive2://hiveserver2:10000/'` 命令时遇到如下异常：
```
localhost:hive wy$ docker exec -it hiveserver2 beeline -u 'jdbc:hive2://hiveserver2:10000/'
...
Connecting to jdbc:hive2://hiveserver2:10000/
25/03/02 08:59:40 [main]: WARN jdbc.HiveConnection: Failed to connect to hiveserver2:10000
Could not open connection to the HS2 server. Please check the server URI and if the URI is correct, then ask the administrator to check the server status.
Error: Could not open client transport with JDBC Uri: jdbc:hive2://hiveserver2:10000/: java.net.ConnectException: Connection refused (Connection refused) (state=08S01,code=0)
Beeline version 3.1.3 by Apache Hive
[WARN] Failed to create directory: /home/hive/.beeline
No such file or directory
```

## 2. 解决方案

排查发现 Hive 的 Docker 配置文件 hadoop-conf 下缺失了 `mapred-site.xml`。`mapred-site.xml` 的缺失导致 HiveServer2 服务未完全启动，间接影响了 Beeline 客户端的用户环境初始化。添加该文件后，HiveServer2 能正常启动并初始化用户环境，使得 Beeline 可以正确创建 `.beeline` 目录。
