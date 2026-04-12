SeaTunnel（原名 Waterdrop）是一个高性能、易扩展的分布式数据集成工具，支持从多种数据源（如 MySQL、Hive、Kafka 等）读取数据，并将数据写入到目标存储（如 ClickHouse、Elasticsearch、控制台等）。在数据集成场景中，MySQL 数据库之间的数据同步是最常见的需求之一。传统的同步方案往往需要编写复杂的 ETL 脚本或依赖重量级的数据同步工具。SeaTunnel 作为新一代分布式数据集成平台，提供了简单、高效、可扩展的解决方案。

本文将以一个实际案例——**将 MySQL 源表数据同步到另一张 MySQL 目标表**，带你深入理解 SeaTunnel Engine 的工作原理和使用方法。

## 1. 环境准备

### 1.1 安装 SeaTunnel

从 SeaTunnel 官网下载最新版本，安装部署请参阅[SeaTunnel 实战：Apache SeaTunnel 本地模式安装与部署](https://smartsi.blog.csdn.net/article/details/140577478)，如果你需要使用 Docker 部署，请参阅[SeaTunnel 实战：使用 Docker Compose 部署 SeaTunnel 集群](https://smartsi.blog.csdn.net/article/details/145813125)。

### 1.2 安装 MySQL JDBC 驱动

SeaTunnel 默认不包含 MySQL 驱动，需手动下载并放入 lib 目录：
```bash
# 创建 lib 目录（如果不存在）
mkdir -p $SEATUNNEL_HOME/lib

# 下载 MySQL JDBC 驱动
cd $SEATUNNEL_HOME/lib
wget https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar

# 验证安装
ls -la $SEATUNNEL_HOME/lib/ | grep mysql
```

### 1.3 准备测试数据

创建 MySQL 源表和目标表：
```sql
-- 创建源表
CREATE TABLE user_source (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(200),
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入测试数据
INSERT INTO user_source (name, email, age) VALUES
('张三', 'zhangsan@example.com', 25),
('李四', 'lisi@example.com', 30),
('王五', 'wangwu@example.com', 28);

-- 创建目标表
CREATE TABLE user_target (
    id BIGINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(200),
    age INT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## 2. 配置 SeaTunnel 任务

### 2.1 创建配置文件

在 SeaTunnel 的 config 目录下创建配置文件 `mysql_to_mysql.conf`，内容如下：
```hocon
# ================================
# 1. SeaTunnel MySQL to MySQL 同步配置
# ================================

# 环境配置
env {
  # 作业模式：BATCH（批处理）或 STREAMING（流处理）
  job.mode = "BATCH"

  # 并行度
  parallelism = 1

  # 检查点间隔（流模式需要）
  # checkpoint.interval = 5000
}

# ================================
# 2. Source 配置 - 读取 MySQL 源表
# ================================
source {
  Jdbc {
    # 必填：结果表名（用于 DAG 连线）
    #result_table_name = "user_source_table"

    # 数据库连接配置
    url = "jdbc:mysql://localhost:3306/test?useSSL=false&serverTimezone=Asia/Shanghai"
    driver = "com.mysql.cj.jdbc.Driver"
    user = "root"
    password = "root"

    # 查询配置
    query = "SELECT id, name, email, age, created_at, updated_at FROM user_source"
  }
}

# ================================
# 3. Transform 配置 - 数据转换（可选）
# ================================
transform {
  # 可选：添加数据转换逻辑
  sql {
    sql = "SELECT id, name, email, age, created_at, updated_at FROM user_source WHERE age > 25"
  }
}

# ================================
# 4. Sink 配置 - 写入 MySQL 目标表
# ================================
sink {
  Jdbc {
    # 源表名（来自 Source 或 Transform）
    #source_table_name = "user_source_table"

    # 数据库连接配置
    url = "jdbc:mysql://localhost:3306/test?useSSL=false&serverTimezone=Asia/Shanghai"
    driver = "com.mysql.cj.jdbc.Driver"
    user = "root"
    password = "root"

    # 目标表配置
    table = "user_target"

    # 写入模式：overwrite（覆盖）或 append（追加）
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
    data_save_mode = "APPEND_DATA"

    # 批量写入配置
    batch_size = 1000

    # 是否自动提交
    # auto_commit = true
  }
}
```
一般情况下，SeaTunnel 的配置文件可以分为以下四个部分：
- env：引擎相关配置
- source：源数据读取配置，在这定义了 MySQL 数据源。
- transform：可选步骤，用于对数据进行过滤或转换。
- sink：写出目标库的配置，在这定义了 MySQL 数据源。

### 2.1 Env：引擎相关配置

如果你只是想一次性把 MySQL 表 A 的数据复制到表 B，JDBC 批处理模式是最简单直接的选择：
```
# 环境配置
env {
  # 作业模式：BATCH（批处理）或 STREAMING（流处理）
  job.mode = "BATCH"

  # 并行度
  parallelism = 1
}
```

### 2.2 数据源配置（Source）

```
source {
  Jdbc {
    # 数据库连接配置
    url = "jdbc:mysql://localhost:3306/test?useSSL=false"
    driver = "com.mysql.cj.jdbc.Driver"
    user = "root"
    password = "root"

    # 查询配置
    query = "SELECT id, name, email, age, created_at, updated_at FROM user_source"
  }
}
```
Source 端的核心参数如下：
- url：必填项，MySQL 数据库连接地址。
- driver：必填项，用于连接远程数据源的 JDBC 类名，对于 MySQL 来说其值为 `com.mysql.cj.jdbc.Driver`。
- user 和 password：数据库用户名和密码。
- query：查询语句。

### 2.3 数据转换（Transform）

```
transform {
  # 可选：添加数据转换逻辑
  sql {
    sql = "SELECT id, name, email, age, created_at, updated_at FROM user_source WHERE age > 25"
  }
}
```
- sql：SQL 查询语句，用于过滤或转换数据。

### 2.4 数据输出（Sink）

```
sink {
  Jdbc {
    # 数据库连接配置
    url = "jdbc:mysql://localhost:3306/test?useSSL=false&serverTimezone=Asia/Shanghai"
    driver = "com.mysql.cj.jdbc.Driver"
    user = "root"
    password = "root"

    # 目标表配置
    database = "test"
    table = "user_target"
    generate_sink_sql=true

    # 写入模式
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
    data_save_mode = "DROP_DATA"

    # 批量写入配置
    batch_size = 1000
  }
}
```
对于 Sink 来说只有两个必填项 url 和 driver，其它根据实际情况选择：
- url：必填项，MySQL 数据库连接地址。
- driver：必填项，用于连接远程数据源的 JDBC 类名，对于 MySQL 来说其值为 `com.mysql.cj.jdbc.Driver`。
- user 和 password：数据库用户名和密码。
- query：使用 sql 语句将上游输入数据写入到数据库。如 `INSERT ...`
- database：使用 database 和 table 自动生成 SQL，并接收上游输入的数据写入数据库。
  - 此选项与 query 选项是互斥的，此选项具有更高的优先级。
- table：使用 database 和 table 自动生成 SQL，并接收上游输入的数据写入数据库。
  - 此选项与 query 选项是互斥的，此选项具有更高的优先级。
  - table 参数可以填入一个任意的表名，这个名字最终会被用作创建表的表名。
- generate_sink_sql：根据要写入的数据库表结构生成 sql 语句
- batch_size：对于批量写入，当缓冲的记录数达到 batch_size 数量或者时间达到 checkpoint.interval 时，数据将被刷新到数据库中
- schema_save_mode：在启动同步任务之前，针对目标侧已有的表结构选择不同的处理方案
  - RECREATE_SCHEMA：当表不存在时会创建，当表已存在时会删除并重建
  - CREATE_SCHEMA_WHEN_NOT_EXIST：当表不存在时会创建，当表已存在时则跳过创建
  - ERROR_WHEN_SCHEMA_NOT_EXIST：当表不存在时将抛出错误
  - IGNORE ：忽略对表的处理
- data_save_mode：在启动同步任务之前，针对目标侧已存在的数据选择不同的处理方案
  - DROP_DATA：保留数据库结构，删除数据
  - APPEND_DATA：保留数据库结构，保留数据
  - CUSTOM_PROCESSING：允许用户自定义数据处理方式
  - ERROR_WHEN_DATA_EXISTS：当有数据时抛出错误
- custom_sql：当 data_save_mode 选择 CUSTOM_PROCESSING 时，需要填写 CUSTOM_SQL 参数
  - 该参数通常填写一条可以执行的 SQL。SQL将在同步任务之前执行

## 3. 运行 SeaTunnel 任务

### 3.1 提交任务

在 SeaTunnel 根目录下运行以下命令提交任务：
```
../bin/seatunnel.sh --config mysql_to_mysql.conf -m local
```

### 3.2 验证结果

任务运行后，查询 MySQL 表数据如下所示：
```sql
-- 查询目标表
SELECT * FROM test.user_target;

+----+-----------+---------------------+------+---------------------+---------------------+
| id | name  | email               | age  | created_at          | updated_at          |
+----+-----------+---------------------+------+---------------------+---------------------+
|  1 | 张三      | zhangsan@example.com|   25 | 2026-04-04 10:00:00 | 2026-04-04 10:00:00 |
|  2 | 李四      | lisi@example.com    |   30 | 2026-04-04 10:00:00 | 2026-04-04 10:00:00 |
|  3 | 王五      | wangwu@example.com  |   28 | 2026-04-04 10:00:00 | 2026-04-04 10:00:00 |
+----+-----------+---------------------+------+---------------------+---------------------+
```

---

## 4. 进阶配置

### 4.1 大数据量并行读取

```hocon
source {
    Jdbc {
        url = "jdbc:mysql://localhost/test?serverTimezone=GMT%2b8"
        driver = "com.mysql.cj.jdbc.Driver"
        connection_check_timeout_sec = 100
        user = "root"
        password = "123456"
        query = "select * from type_bin"
        partition_column = "id"
        split.size = 10000
    }
}
```
