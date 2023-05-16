## 1. 查询 User 表汇总所有的数据

- 创建 User 表，添加数据
- 创建模块，导致坐标
- 编写 Mybatis 核心配置文件：替换连接信息，解决硬编码问题
- 编写 SQL 映射文件：统一管理 SQL 语句，解决硬编码问题
- 编码
  - 定义 POJO 类
  - 加载核心配置文件，获取 SqlSessionFactory 对象
  - 获取 SqlSession 对象，执行 SQL 语句
  - 释放资源


```sql
CREATE DATABASE IF NOT EXISTS test;
USE test;

CREATE TABLE IF NOT EXISTS `tb_user` (
  `id` bigint(20) NOT NULL COMMENT '主键ID',
  `name` varchar(30) DEFAULT NULL COMMENT '姓名',
  `age` int(11) DEFAULT NULL COMMENT '年龄',
  `email` varchar(50) DEFAULT NULL COMMENT '邮箱',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
```

如果使用 Maven 来构建项目，则需将下面的依赖代码置于 pom.xml 文件中：
```xml
<dependency>
    <groupId>org.mybatis</groupId>
    <artifactId>mybatis</artifactId>
    <version>3.5.11</version>
</dependency>
```

配置 mybatis-config.xml 配置文件：
```xml

```
