本文展示了如何使用 Flink CDC 快速构建 MySQL 和 Postgres 上的 Streaming ETL。

假设我们经营的是电子商务业务，商品和订单数据存储在 MySQL 中，与订单相关的物流信息存储在 Postgres 中。我们希望使用商品和物流表来充实订单，即订单表关联其对应的商品和物流信息构建一张宽表，然后将充实后的订单实时写到 ElasticSearch 中。

在接下来的内容中，我们将介绍如何使用 Flink Mysql/Postgres CDC 来实现上述需求。本教程中的所有练习都是在 Flink SQL CLI 中执行的，整个过程使用的是标准的 SQL 语法，没有任何一行 Java/Scala 代码，也无需安装 IDE。

> 本教程的演示基于 Docker 环境


架构概述如下：

![](https://nightlies.apache.org/flink/flink-cdc-docs-release-3.5/fig/mysql-postgres-tutorial/flink-cdc-streaming-etl.png)

## 1. 准备阶段

准备一台安装了 Docker 的 Linux 或 MacOS 计算机。

### 1.1 准备教程所需要的组件

接下来的教程将以 docker-compose 的方式准备所需要的组件。使用如下的内容创建一个 `docker-compose.yml` 文件：
```
version: '2.1'
services:
  postgres:
    image: debezium/example-postgres:1.1
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
  mysql:
    image: debezium/example-mysql:1.1
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=123456
      - MYSQL_USER=mysqluser
      - MYSQL_PASSWORD=mysqlpw
  elasticsearch:
    image: elastic/elasticsearch:7.6.0
    environment:
      - cluster.name=docker-cluster
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - discovery.type=single-node
    ports:
      - "9200:9200"
      - "9300:9300"
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
  kibana:
    image: elastic/kibana:7.6.0
    ports:
      - "5601:5601"
```
该 Docker Compose 中包含的容器有：
- MySQL：商品表 `products` 和 订单表 `orders` 存储在该数据库中，这两张表将和 Postgres 数据库中的物流表 shipments 进行关联，得到一张包含更多信息的订单表 `enriched_orders`；
- Postgres：物流表 `shipments` 存储在该数据库中；
- Elasticsearch：主要用作数据接收器来存储订单表 `enriched_orders`；
- Kibana：用来可视化 ElasticSearch 的数据。

在 `docker-compose.yml` 所在目录下执行如下命令来启动所有容器：
```
docker-compose up -d
```

该命令将以 detached 模式自动启动 Docker Compose 配置中定义的所有容器。你可以通过 `docker ps` 命令来查看上述容器是否正常启动了，也可以通过访问 `http://localhost:5601/` 来查看 Kibana 是否运行正常。

### 1.2 下载 Flink 和所需要的依赖包

- 下载 Flink [1.20.2]() 并将其解压至目录 flink-1.20.2，
- 下载下面列出的依赖包，并将它们放到目录 `flink-1.20.2/lib/` 下
  - [flink-sql-connector-elasticsearch7-3.1.0-1.20.jar](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-elasticsearch7/3.1.0-1.20/flink-sql-connector-elasticsearch7-3.1.0-1.20.jar)
  - [flink-sql-connector-mysql-cdc-3.5.0.jar](https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mysql-cdc/3.5.0/flink-sql-connector-mysql-cdc-3.5.0.jar)
  - [flink-sql-connector-postgres-cdc-3.5.0.jar](https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-postgres-cdc/3.5.0/flink-sql-connector-postgres-cdc-3.5.0.jar)

### 1.3  准备数据

#### 1.3.1 在 MySQL 数据库中准备数据

第一步入 MySQL 容器：
```
docker-compose exec mysql mysql -uroot -p123456
```
第二步创建数据库和表 `products`，`orders`，并插入数据：
```sql
-- MySQL
CREATE DATABASE mydb;
USE mydb;
CREATE TABLE products (
  id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description VARCHAR(512)
);
ALTER TABLE products AUTO_INCREMENT = 101;

INSERT INTO products
VALUES (default,"scooter","Small 2-wheel scooter"),
       (default,"car battery","12V car battery"),
       (default,"12-pack drill bits","12-pack of drill bits with sizes ranging from #40 to #3"),
       (default,"hammer","12oz carpenter's hammer"),
       (default,"hammer","14oz carpenter's hammer"),
       (default,"hammer","16oz carpenter's hammer"),
       (default,"rocks","box of assorted rocks"),
       (default,"jacket","water resistent black wind breaker"),
       (default,"spare tire","24 inch spare tire");

CREATE TABLE orders (
  order_id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
  order_date DATETIME NOT NULL,
  customer_name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 5) NOT NULL,
  product_id INTEGER NOT NULL,
  order_status BOOLEAN NOT NULL -- Whether order has been placed
) AUTO_INCREMENT = 10001;

INSERT INTO orders
VALUES (default, '2020-07-30 10:08:22', 'Jark', 50.50, 102, false),
       (default, '2020-07-30 10:11:09', 'Sally', 15.00, 105, false),
       (default, '2020-07-30 12:00:30', 'Edward', 25.25, 106, false);
```
#### 1.3.2 在 Postgres 数据库中准备数据

第一步进入 Postgres 容器：
```
docker-compose exec postgres psql -h localhost -U postgres
```
第二步创建数据库和表 `shipments` 并插入数据：
```sql
-- PG
CREATE TABLE shipments (
  shipment_id SERIAL NOT NULL PRIMARY KEY,
  order_id SERIAL NOT NULL,
  origin VARCHAR(255) NOT NULL,
  destination VARCHAR(255) NOT NULL,
  is_arrived BOOLEAN NOT NULL
);

ALTER SEQUENCE public.shipments_shipment_id_seq RESTART WITH 1001;
ALTER TABLE public.shipments REPLICA IDENTITY FULL;
INSERT INTO shipments
VALUES (default,10001,'Beijing','Shanghai',false),
       (default,10002,'Hangzhou','Shanghai',false),
       (default,10003,'Shanghai','Hangzhou',false);
```

## 2. 启动 Flink 集群和 Flink SQL CLI

首先使用下面的命令跳转至 Flink 目录下：
```
cd flink-1.20.2
```
然后使用下面的命令启动 Flink 集群：
```
./bin/start-cluster.sh
```

启动成功的话，可以在 `http://localhost:8081/` 访问到 Flink Web UI，如下所示：

![]()

使用下面的命令启动 Flink SQL CLI
```
./bin/sql-client.sh
```
启动成功后，可以看到如下的页面：

![]()

## 3. 在 Flink SQL CLI 中使用 Flink DDL 创建表

首先，开启 checkpoint，每隔 3 秒做一次 checkpoint。
```sql
-- Flink SQL
Flink SQL> SET execution.checkpointing.interval = 3s;
[INFO] Execute statement succeeded.
```
然后, 对于数据库中的表 `products`, `orders`, `shipments`，使用 Flink SQL CLI 创建对应的表，用于同步这些底层数据库表的数据。
```sql
-- Flink SQL
Flink SQL> CREATE TABLE products (
    id INT,
    name STRING,
    description STRING,
    PRIMARY KEY (id) NOT ENFORCED
  ) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'localhost',
    'port' = '3306',
    'username' = 'root',
    'password' = '123456',
    'database-name' = 'mydb',
    'table-name' = 'products'
  );

Flink SQL> CREATE TABLE orders (
   order_id INT,
   order_date TIMESTAMP(0),
   customer_name STRING,
   price DECIMAL(10, 5),
   product_id INT,
   order_status BOOLEAN,
   PRIMARY KEY (order_id) NOT ENFORCED
 ) WITH (
   'connector' = 'mysql-cdc',
   'hostname' = 'localhost',
   'port' = '3306',
   'username' = 'root',
   'password' = '123456',
   'database-name' = 'mydb',
   'table-name' = 'orders'
 );

Flink SQL> CREATE TABLE shipments (
   shipment_id INT,
   order_id INT,
   origin STRING,
   destination STRING,
   is_arrived BOOLEAN,
   PRIMARY KEY (shipment_id) NOT ENFORCED
 ) WITH (
   'connector' = 'postgres-cdc',
   'hostname' = 'localhost',
   'port' = '5432',
   'username' = 'postgres',
   'password' = 'postgres',
   'database-name' = 'postgres',
   'schema-name' = 'public',
   'table-name' = 'shipments',
   'slot.name' = 'flink'
 );
```
最后，创建 `enriched_orders` 表，用来将关联后的订单数据写入 Elasticsearch 中：
```sql
-- Flink SQL
Flink SQL> CREATE TABLE enriched_orders (
   order_id INT,
   order_date TIMESTAMP(0),
   customer_name STRING,
   price DECIMAL(10, 5),
   product_id INT,
   order_status BOOLEAN,
   product_name STRING,
   product_description STRING,
   shipment_id INT,
   origin STRING,
   destination STRING,
   is_arrived BOOLEAN,
   PRIMARY KEY (order_id) NOT ENFORCED
 ) WITH (
     'connector' = 'elasticsearch-7',
     'hosts' = 'http://localhost:9200',
     'index' = 'enriched_orders'
);
```
## 4. 关联订单数据将其写入 Elasticsearch 中

使用 Flink SQL 将订单表 `order` 与 商品表 `products`，物流表 `shipments` 关联，并将关联后的订单信息写入 Elasticsearch 中：
```sql
-- Flink SQL
Flink SQL> INSERT INTO enriched_orders
 SELECT o.*, p.name, p.description, s.shipment_id, s.origin, s.destination, s.is_arrived
 FROM orders AS o
 LEFT JOIN products AS p ON o.product_id = p.id
 LEFT JOIN shipments AS s ON o.order_id = s.order_id;
```


...
