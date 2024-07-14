


```sql
CREATE TABLE IF NOT EXISTS `profile_meta_entity_type`(
    `id` BIGINT UNSIGNED AUTO_INCREMENT COMMENT '自增ID',
    `status` INT NOT NULL DEFAULT 1 COMMENT '状态:1-启用,2-停用',
    `entity_type_id` VARCHAR(40) NOT NULL COMMENT '实体类型ID',
    `entity_type_name` VARCHAR(100) NOT NULL COMMENT '实体类型名称',
    `source_type` INT NOT NULL DEFAULT 1 COMMENT '创建方式: 1-系统内置,2-自定义',
    `creator` VARCHAR(100) NOT NULL COMMENT '创建者',
    `modifier` VARCHAR(100) NOT NULL COMMENT '修改者',
    `gmt_create` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `gmt_modified` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
    PRIMARY KEY (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '画像-实体类型';
```
当前时间为 `2024-07-14 09:06:41` 而 `gmt_create` 设置的时间为 `2024-07-14 01:06:41`。MySQL服务器、客户端以及应用程序可能会在不同的时区运行。MySQL的CURRENT_TIMESTAMP是基于服务器的系统时区来获取当前时间的。如果服务器和应用程序的时区设置不一致，就可能导致时间戳的显示或处理出现问题。

## 2. 解决方案

确保MySQL服务器和客户端的时区设置一致。可以通过以下SQL命令查看或设置时区：
```
SELECT @@global.time_zone, @@session.time_zone;
```
设置时区（例如设置为东八区，即中国标准时间）：
```
SET GLOBAL time_zone = '+8:00';
SET time_zone = '+8:00';

```
如果不希望改变MySQL的全局时区设置，可以在应用程序层面进行时区转换。如果使用 JDBC 连接MySQL，可以在连接字符串中指定时区属性：
```
jdbc:mysql://host:port/database?serverTimezone=UTC
```


https://zhuanlan.zhihu.com/p/593401994?utm_id=0
https://blog.csdn.net/JSUITDLWXL/article/details/120082244
https://blog.csdn.net/a1468660798/article/details/134557163
https://blog.51cto.com/u_16213380/8547907






...
