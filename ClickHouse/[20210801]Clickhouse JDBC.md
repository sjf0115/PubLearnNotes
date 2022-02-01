

```xml
<dependency>
    <groupId>ru.yandex.clickhouse</groupId>
    <artifactId>clickhouse-jdbc</artifactId>
    <version>0.3.0</version>
</dependency>
```

```xml
<dependency>
    <groupId>com.github.housepower</groupId>
    <artifactId>clickhouse-native-jdbc</artifactId>
    <version>1.6-stable</version>
</dependency>
```







两者间的主要区别如下：
- 驱动类加载路径不同，分别为 ru.yandex.clickhouse.ClickHouseDriver 和 com.github.housepower.jdbc.ClickHouseDriver
- 默认连接端口不同，分别为 8123 和 9000
- 连接协议不同，官方驱动使用 HTTP 协议，而三方驱动使用 TCP 协议
