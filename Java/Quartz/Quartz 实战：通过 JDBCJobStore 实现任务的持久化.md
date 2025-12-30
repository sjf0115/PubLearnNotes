在现代企业级应用中，任务调度是不可或缺的基础设施。Quartz 作为 Java 领域最成熟的任务调度框架之一，提供了强大而灵活的调度能力。其中，JobStore 是实现调度持久化的核心组件，而 JdbcJobStore 正是将 Quartz 与关系型数据库集成的关键桥梁。本文将深入探讨 JdbcJobStore 的工作原理、配置方式和最佳实践。


## 1. 为什么需要 JobStore 持久化？
在深入了解 JdbcJobStore 之前，我们先明确持久化存储的必要性：

1.1 RAMJobStore 的局限性
默认的 RAMJobStore 将所有调度数据存储在内存中，这种方案存在明显缺陷：

数据易失性：应用重启后所有调度信息丢失

缺乏集群支持：多节点无法共享调度状态

无法恢复任务：系统崩溃后无法继续未完成的任务

1.2 JdbcJobStore 的优势
JdbcJobStore 通过数据库持久化解决了上述问题：

数据持久化：调度信息在数据库中长期保存

集群支持：多节点共享数据库，实现负载均衡和故障转移

事务支持：确保调度操作的原子性和一致性

恢复能力：系统重启后可恢复任务执行

https://github.com/quartz-scheduler/quartz/releases/tag/v2.5.0
```
quartz-2.4.1/quartz/src/main/resources/org/quartz/impl/jdbcjobstore/
```

## 2. 初始化数据库

```
drop database quartz;
create database quartz;
```

```
source ~/Downloads/quartz-2.5.0/quartz/src/main/resources/org/quartz/impl/jdbcjobstore/tables_mysql_innodb.sql
source ~/Downloads/quartz-2.3.2/quartz-core/src/main/resources/org/quartz/impl/jdbcjobstore/tables_mysql_innodb.sql
```

```
mysql> show tables;
+--------------------------+
| Tables_in_quartz         |
+--------------------------+
| QRTZ_BLOB_TRIGGERS       |
| QRTZ_CALENDARS           |
| QRTZ_CRON_TRIGGERS       |
| QRTZ_FIRED_TRIGGERS      |
| QRTZ_JOB_DETAILS         |
| QRTZ_LOCKS               |
| QRTZ_PAUSED_TRIGGER_GRPS |
| QRTZ_SCHEDULER_STATE     |
| QRTZ_SIMPLE_TRIGGERS     |
| QRTZ_SIMPROP_TRIGGERS    |
| QRTZ_TRIGGERS            |
+--------------------------+
11 rows in set (0.00 sec)
```

## 3. 实战

```xml
<properties>
    <spring.quartz.version>2.7.5</spring.quartz.version>
    <spring.mybatis.version>2.3.2</mybatis.spring.version>
    <mysql.version>5.1.46</mysql.version>
</properties>

<dependencies>
    <!-- Web开发需要的起步依赖 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- 集成 Quartz -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-quartz</artifactId>
        <version>${spring.quartz.version}</version>
    </dependency>

    <!-- 集成 Mybatis -->
    <dependency>
        <groupId>org.mybatis.spring.boot</groupId>
        <artifactId>mybatis-spring-boot-starter</artifactId>
        <version>${spring.mybatis.version}</version>
    </dependency>

    <!-- MySQL -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
        <version>${mysql.version}</version>
    </dependency>
</dependencies>
```


```yaml
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/quartz?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true
    username: root
    password: root

  quartz:
    job-store-type: jdbc
    jdbc:
      initialize-schema: always
```



```
[INFO]  [quartzScheduler_Worker-1] c.s.e.j.StoreJob - Welcome to Quartz: 1
[INFO]  [quartzScheduler_Worker-2] c.s.e.j.StoreJob - Welcome to Quartz: 2
[INFO]  [quartzScheduler_Worker-3] c.s.e.j.StoreJob - Welcome to Quartz: 3
```

```yaml
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/quartz?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true
    username: root
    password: root

  quartz:
    job-store-type: jdbc
    jdbc:
      initialize-schema: never
```


```
[INFO]  [quartzScheduler_Worker-1] c.s.e.j.StoreJob - Welcome to Quartz: 4
[INFO]  [quartzScheduler_Worker-2] c.s.e.j.StoreJob - Welcome to Quartz: 5
[INFO]  [quartzScheduler_Worker-3] c.s.e.j.StoreJob - Welcome to Quartz: 6
```
