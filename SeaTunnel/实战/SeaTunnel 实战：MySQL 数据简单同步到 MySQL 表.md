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

```
# 环境配置
env {
  # 作业模式：BATCH（批处理）或 STREAMING（流处理）
  job.mode = "BATCH"

  # 并行度
  parallelism = 1

  # 检查点间隔（流模式需要）
  # checkpoint.interval = 5000
}
```

### 2.2 数据源配置（Source）

```
source {
  Jdbc {
    # 必填：结果表名（用于 DAG 连线）
    result_table_name = "user_source_table"

    # 数据库连接配置
    url = "jdbc:mysql://localhost:3306/test?useSSL=false&serverTimezone=Asia/Shanghai"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "root"
    password = "root"

    # 查询配置
    query = "SELECT id, name, email, age, created_at, updated_at FROM user_source"

    # 分片配置（大数据量时启用）
    # partition_column = "id"
    # partition_num = 4

    # 并行读取配置
    # parallelism = 2
  }
}
```
- url：必填项，MySQL 数据库连接地址。
- driver：必填项，用于连接远程数据源的 JDBC 类名，对于 MySQL 来说其值为 `com.mysql.cj.jdbc.Driver`。
- user 和 password：数据库用户名和密码。
- query：查询语句。
- table：需要同步的表名。
- result_table_name：结果表名称，用于后续步骤引用。

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
source {
  Jdbc {
    # 必填：结果表名（用于 DAG 连线）
    result_table_name = "user_source_table"

    # 数据库连接配置
    url = "jdbc:mysql://localhost:3306/test?useSSL=false&serverTimezone=Asia/Shanghai"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "root"
    password = "root"

    # 查询配置
    query = "SELECT id, name, email, age, created_at, updated_at FROM user_source"

    # 分片配置（大数据量时启用）
    # partition_column = "id"
    # partition_num = 4

    # 并行读取配置
    # parallelism = 2
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







## 3. 运行 SeaTunnel 任务

### 3.1 提交任务

在 SeaTunnel 根目录下运行以下命令提交任务：
```
bin/seatunnel.sh --config profile/mysql_to_mysql.conf
```

本地模式执行:
```bash
# 执行作业
bin/seatunnel.sh --config profile/mysql_to_mysql.conf

# 带详细日志执行
/bin/seatunnel.sh --config profile/mysql_to_mysql.conf --deploy-mode client
```

集群模式执行:
```bash
# 启动 SeaTunnel 集群
bin/seatunnel-cluster.sh -d

# 提交作业到集群
bin/seatunnel.sh profile/mysql_to_mysql.conf --deploy-mode cluster
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
    url = "jdbc:mysql://localhost:3306/source_db"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "root"
    password = "your_password"

    # 并行读取配置
    query = "SELECT * FROM large_table WHERE id >= ? AND id < ?"
    partition_column = "id"
    partition_num = 8

    # 每个分区的范围
    # SeaTunnel 会自动计算分区范围
  }
}
```

### 4.2 增量同步（CDC 模式）

```hocon
source {
  MySQL-CDC {
    result_table_name = "cdc_source"

    # 数据库配置
    hostname = "localhost"
    port = 3306
    username = "root"
    password = "your_password"
    database = "source_db"
    table = ["user_source"]

    # CDC 配置
    server_id = 5656
    server_timezone = "Asia/Shanghai"

    # 起始位置
    # startup_mode = "initial"        # 从头开始
    # startup_mode = "latest-offset"  # 从最新位置开始
  }
}

sink {
  Jdbc {
    source_table_name = "cdc_source"
    url = "jdbc:mysql://localhost:3306/target_db"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "root"
    password = "your_password"
    table = "user_target"

    # 支持 INSERT/UPDATE/DELETE
    # 根据 CDC 事件自动处理
  }
}
```

### 4.3 数据转换示例

```hocon
transform {
  # 字段过滤
  Filter {
    source_table_name = "user_source_table"
    result_table_name = "filtered_data"
    fields = ["id", "username", "email"]
  }

  # 字段值替换
  Replace {
    source_table_name = "filtered_data"
    result_table_name = "transformed_data"
    replace_field = "email"
    pattern = "@example.com"
    replacement = "@newdomain.com"
  }
}

sink {
  Jdbc {
    source_table_name = "transformed_data"
    # ... 其他配置
  }
}
```

---

## 5. 常见问题与解决方案

### 5.1 驱动缺失问题

**错误**：
```
java.lang.NoClassDefFoundError: com/mysql/cj/MysqlType
```

**解决方案**：
```bash
# 安装 MySQL JDBC 驱动
wget -O $SEATUNNEL_HOME/lib/mysql-connector-j-8.0.33.jar \
  https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar
```

### 5.2 连接超时问题

**错误**：
```
Communications link failure
```

**解决方案**：
```hocon
# 在 JDBC URL 中添加超时参数
url = "jdbc:mysql://localhost:3306/source_db?connectTimeout=60000&socketTimeout=60000"
```

### 5.3 字符编码问题

**错误**：
```
Incorrect string value
```

**解决方案**：
```hocon
# 在 JDBC URL 中指定编码
url = "jdbc:mysql://localhost:3306/source_db?useUnicode=true&characterEncoding=UTF-8"
```

---


https://www.whaleops.com/846839-846849_3628105.html
