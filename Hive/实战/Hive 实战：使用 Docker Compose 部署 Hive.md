
```yml
version: '3.9'
services:
  # Hive Metastore 服务
  hive-metastore:
    image: apache/hive:3.1.2
    container_name: docker_metastore
    #restart: unless-stopped
    env_file:
      - hive.env
    environment:
      DB_DRIVER: postgres
      SERVICE_NAME: 'metastore'
      SERVICE_OPTS: '-Xmx1G -Djavax.jdo.option.ConnectionDriverName=org.postgresql.Driver
                     -Djavax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/metastore_db
                     -Djavax.jdo.option.ConnectionUserName=hive
                     -Djavax.jdo.option.ConnectionPassword=password'
    ports:
        - '9083:9083' # 默认端口用于metastore服务
    volumes:
        - warehouse:/opt/hive/data/warehouse
        - type: bind
          source: ${POSTGRES_LOCAL_PATH}
          target: /opt/hive/lib/postgres.jar
    networks:
      - hive
    #command: /opt/hive/bin/start-metastore

  # Hive Server服务
  hiveserver2:
    image: apache/hive:3.1.2
    container_name: docker_hiveserver2
    depends_on:
      - hive-metastore
    #restart: unless-stopped
    env_file:
      - hive.env
    environment:
      HIVE_SERVER2_THRIFT_PORT: 10000
      SERVICE_OPTS: '-Xmx1G -Dhive.metastore.uris=thrift://metastore:9083'
      IS_RESUME: 'true'
      SERVICE_NAME: 'hiveserver2'
    ports: # 默认端口用于HiveServer2服务
      - '10000:10000'
      - '10002:10002'
    volumes:
      - warehouse:/opt/hive/data/warehouse
    networks:
      - pub-network
    #command: /opt/hive/bin/hive --service hiveserver2 --hiveconf hive.server2.thrift.bind.host hive-server --hiveconf hive.server2.thrift.port=10000 --hiveconf hive.metastore.uris=thrift://hive-metastore:9083

volumes:
  hive-db:
  warehouse:

networks:  # 网络
  pub-network:
      external: true
```



```xml
# Metastore服务数据库的配置
HIVE_METASTORE_DB_TYPE=postgres
HIVE_METASTORE_DB_DRIVER=org.postgresql.Driver
HIVE_METASTORE_DB_USERNAME=postgres
HIVE_METASTORE_DB_PASSWORD=root
HIVE_METASTORE_DB_HOSTNAME=postgres_db
HIVE_METASTORE_DB_PORT=5432
HIVE_METASTORE_DB_NAME=hive_db

# HDFS配置（假设Hadoop集群已经部署）
HIVE_CONF_fs_defaultFS=hdfs://namenode:9870
HIVE_CONF_hive_metastore_uris=thrift://hive-metastore:9083
```



...
