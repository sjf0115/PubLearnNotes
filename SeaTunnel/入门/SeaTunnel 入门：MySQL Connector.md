


> 通过 JDBC 读取外部数据源数据。

## 1. 支持 Mysql 版本

5.5/5.6/5.7/8.0/8.1/8.2/8.3/8.4

## 支持的引擎
- Spark
- Flink
- SeaTunnel Zeta

## 需要的依赖项

- 对于 Spark/Flink 引擎
  - 您需要确保 jdbc 驱动程序 jar 包 已放置在目录 `${SEATUNNEL_HOME}/plugins/` 中。
- 对于 SeaTunnel Zeta 引擎
  - 您需要确保 jdbc 驱动程序 jar 包 已放置在目录 `${SEATUNNEL_HOME}/lib/` 中。





前置准备在开始之前，请确保已经下载了对应版本的 MySQL JDBC 驱动 mysql-connector-java-xxx.jar，并将其放置在 SeaTunnel 的安装目录下的 lib 文件夹中。可以从以下链接获取：https://mvnrepository.com/artifact/mysql/mysql-connector-java

对于使用 Spark 或 Flink 的 SeaTunnel 任务，也需要将该 JAR 包复制到相应的目录下：
- Spark:  `$SPARK_HOME/jars/`
- Flink:  `$FLINK_HOME/lib/`
