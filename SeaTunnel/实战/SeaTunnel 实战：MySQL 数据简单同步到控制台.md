SeaTunnel（原名 Waterdrop）是一个高性能、易扩展的分布式数据集成工具，支持从多种数据源（如 MySQL、Hive、Kafka 等）读取数据，并将数据写入到目标存储（如 ClickHouse、Elasticsearch、控制台等）。本文将详细介绍如何使用 SeaTunnel 将 MySQL 数据同步到控制台，并附上完整的配置和代码示例。

## 1. 环境准备

### 1.1 安装 SeaTunnel

从 SeaTunnel 官网 下载最新版本，或使用以下命令安装：


### 1.2 安装 MySQL 驱动

SeaTunnel 默认不包含 MySQL 驱动，需手动下载并放入 lib 目录：
```shell
wget https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.26/mysql-connector-java-8.0.26.jar
cp mysql-connector-java-8.0.26.jar lib/
```

## 2. 配置 SeaTunnel 任务

### 2.1 创建配置文件

在 SeaTunnel 的 config 目录下创建配置文件 `mysql_to_console.conf`，内容如下：
```yaml
env {
  execution.parallelism = 1
  job.mode = "BATCH"
}

source {
  MySQL {
    url = "jdbc:mysql://localhost:3306/test"
    username = "root"
    password = "root"
    table = "tb_user"
    result_table_name = "mysql_tb_user"
  }
}

transform {
  # 可选：添加数据转换逻辑
  sql {
    sql = "SELECT id, name, age FROM mysql_tb_user WHERE age > 18"
  }
}

sink {
  Console {
    limit = 100  # 限制输出到控制台的行数
  }
}
```

### 2.2 配置说明

- source：定义 MySQL 数据源，指定连接信息、表名和结果表名称。
- transform：可选步骤，用于对数据进行过滤或转换。
- sink：定义控制台输出，限制输出行数以避免数据过多。

#### 2.2.1 数据源配置（Source）

```yaml
source {
  MySQL {
    url = "jdbc:mysql://localhost:3306/test"
    username = "root"
    password = "root"
    table = "tb_user"
    result_table_name = "mysql_tb_user"
  }
}
```
- url：MySQL 数据库连接地址。
- username 和 password：数据库用户名和密码。
- table：需要同步的表名。
- result_table_name：结果表名称，用于后续步骤引用。

#### 2.2.2 数据转换（Transform）

```yaml
transform {
  # 可选：添加数据转换逻辑
  sql {
    sql = "SELECT id, name, age FROM mysql_tb_user WHERE age > 18"
  }
}
```
- sql：SQL 查询语句，用于过滤或转换数据。

#### 2.2.3 数据输出（Sink）

```yaml
sink {
  Console {
    limit = 100  # 限制输出到控制台的行数
  }
}
```
- limit：限制输出到控制台的行数，避免数据过多。


## 3. 运行 SeaTunnel 任务

### 3.1 提交任务

在 SeaTunnel 根目录下运行以下命令提交任务：
```
bin/seatunnel.sh --config conf/mysql_to_console.conf
```

### 3.2 查看输出

任务运行后，SeaTunnel 会将 MySQL 数据输出到控制台，示例如下：
```
+----+--------+-----+
| id | name   | age |
+----+--------+-----+
| 1  | Alice  | 20  |
| 2  | Bob    | 22  |
| 3  | Charlie| 25  |
+----+--------+-----+
```
