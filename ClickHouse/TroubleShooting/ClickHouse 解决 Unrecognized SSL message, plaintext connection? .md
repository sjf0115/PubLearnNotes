

## 1. 问题

在使用 Java JDBC 驱动连接 ClickHouse：
```
String url = "jdbc:ch:https://localhost:8123/default";
Properties properties = new Properties();
properties.setProperty("user", "default");
properties.setProperty("password", "");

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection()) {
    String catalog = connection.getCatalog();
    System.out.println("Connected to ClickHouse " + catalog + " Successful !");
} catch (SQLException e) {
    e.printStackTrace();
}
```
出现如下异常：
```java
java.sql.SQLException: Unrecognized SSL message, plaintext connection?
	at com.clickhouse.jdbc.SqlExceptionUtils.handle(SqlExceptionUtils.java:85)
	at com.clickhouse.jdbc.SqlExceptionUtils.create(SqlExceptionUtils.java:31)
	at com.clickhouse.jdbc.SqlExceptionUtils.handle(SqlExceptionUtils.java:90)
	at com.clickhouse.jdbc.internal.ClickHouseConnectionImpl.getServerInfo(ClickHouseConnectionImpl.java:123)
	at com.clickhouse.jdbc.internal.ClickHouseConnectionImpl.<init>(ClickHouseConnectionImpl.java:331)
	at com.clickhouse.jdbc.DataSourceV1.getConnection(DataSourceV1.java:46)
	at com.clickhouse.jdbc.DataSourceV1.getConnection(DataSourceV1.java:16)
	at com.clickhouse.jdbc.ClickHouseDataSource.getConnection(ClickHouseDataSource.java:32)
	at com.example.jdbc.crud.ConnectionExample.main(ConnectionExample.java:23)
Caused by: java.net.ConnectException: Unrecognized SSL message, plaintext connection?
	at com.clickhouse.client.http.ApacheHttpConnectionImpl.post(ApacheHttpConnectionImpl.java:307)
	at com.clickhouse.client.http.ClickHouseHttpClient.send(ClickHouseHttpClient.java:195)
	at com.clickhouse.client.AbstractClient.execute(AbstractClient.java:280)
	at com.clickhouse.client.ClickHouseClientBuilder$Agent.sendOnce(ClickHouseClientBuilder.java:282)
	at com.clickhouse.client.ClickHouseClientBuilder$Agent.send(ClickHouseClientBuilder.java:294)
	at com.clickhouse.client.ClickHouseClientBuilder$Agent.execute(ClickHouseClientBuilder.java:349)
	at com.clickhouse.client.ClickHouseClient.executeAndWait(ClickHouseClient.java:881)
	at com.clickhouse.client.ClickHouseRequest.executeAndWait(ClickHouseRequest.java:2154)
	at com.clickhouse.jdbc.internal.ClickHouseConnectionImpl.getServerInfo(ClickHouseConnectionImpl.java:120)
	... 5 more
```
该错误表明客户端与服务端在 SSL/TLS 握手过程中出现协议不匹配，通常由加密通信配置错误导致。



解决方案:
```
String url = "jdbc:ch:http://localhost:8123/default";
```



---

## 2. 错误原因全解析

### 2.1 根本原因
- **协议不匹配**：客户端尝试使用 SSL 连接，但服务端未启用 SSL（或反之）
- **数据流混淆**：客户端预期接收加密数据，但服务端返回明文数据

### 2.2 具体触发场景
| 场景 | 客户端配置 | 服务端实际状态 | 结果 |
|------|------------|----------------|------|
| 1 | `jdbc:ch:https://...` | 未启用 SSL | 客户端尝试 SSL 握手，服务端返回明文响应 |
| 2 | `jdbc:ch:http://...` | 强制 SSL | 服务端期待 SSL 握手，客户端发送明文请求 |
| 3 | 中间代理干扰 | 代理未正确转发 | 代理返回非 SSL 响应 |
| 4 | 证书配置错误 | 自签名证书未受信 | SSL 握手失败后降级明文 |

---

## 三、分步诊断流程

### 3.1 第一步：验证服务端状态
```bash
# 检查ClickHouse端口监听情况
netstat -tuln | grep 8123

# 预期输出（未启用SSL）：
# tcp6 0 0 :::8123 :::* LISTEN

# 启用SSL后的输出应显示SSL特征端口（如8443）
```

### 3.2 第二步：使用命令行工具测试
```bash
# 明文连接测试
clickhouse-client --host ch-host --port 8123 --user default

# SSL连接测试（需服务端配置）
clickhouse-client --host ch-host --port 8443 --secure --user default
```

### 3.3 第三步：CURL 验证
```bash
# 测试HTTP端口
curl http://ch-host:8123 -d "SELECT 1"

# 测试HTTPS端口（需有效证书）
curl -k https://ch-host:8443 -d "SELECT 1"
```

---

## 四、8种解决方案详解

### 4.1 方案一：统一协议配置
**适用场景**：客户端与服务端协议不匹配

**客户端配置调整**：
```java
// 禁用SSL（服务端未启用）
String url = "jdbc:ch:http://ch-host:8123/db";

// 强制启用SSL（服务端已配置）
String url = "jdbc:ch:https://ch-host:8443/db?ssl=true";
```

### 4.2 方案二：服务端SSL配置修复
**服务端配置示例（/etc/clickhouse-server/config.d/ssl.xml）**：
```xml
<clickhouse>
    <openSSL>
        <server>
            <certificateFile>/path/to/server.crt</certificateFile>
            <privateKeyFile>/path/to/server.key</privateKeyFile>
            <caConfig>/path/to/ca.crt</caConfig>
            <verificationMode>none</verificationMode> <!-- 测试环境可关闭验证 -->
        </server>
    </openSSL>
</clickhouse>
```
**重启服务**：
```bash
systemctl restart clickhouse-server
```

### 4.3 方案三：客户端信任自签名证书
**Java信任存储操作**：
```bash
# 提取服务端证书
openssl s_client -connect ch-host:8443 </dev/null | openssl x509 > server.crt

# 导入到Java信任库
keytool -importcert -alias clickhouse -file server.crt \
    -keystore $JAVA_HOME/lib/security/cacerts -storepass changeit
```

### 4.4 方案四：明确禁用SSL验证
```java
Properties props = new Properties();
props.setProperty("ssl", "true");
props.setProperty("sslMode", "NONE"); // 不验证证书
props.setProperty("sslRootCertificate", "/path/to/ca.crt");

ClickHouseDataSource ds = new ClickHouseDataSource(url, props);
```

### 4.5 方案五：修复中间代理配置
**Nginx代理示例（SSL Termination）**：
```nginx
server {
    listen 8443 ssl;
    server_name ch-proxy;

    ssl_certificate /path/to/server.crt;
    ssl_certificate_key /path/to/server.key;

    location / {
        proxy_pass http://ch-host:8123; # 转发到明文端口
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 4.6 方案六：驱动版本升级
**Maven配置**：
```xml
<dependency>
    <groupId>com.clickhouse</groupId>
    <artifactId>clickhouse-jdbc</artifactId>
    <version>0.4.6</version>
    <classifier>all</classifier>
</dependency>
```

### 4.7 方案七：网络抓包分析
```bash
tcpdump -i eth0 -s 0 -w clickhouse.pcap port 8123 or port 8443
```
使用 Wireshark 分析 TLS 握手过程：
1. 检查 Client Hello 是否发送
2. 验证 Server Hello 响应
3. 确认证书交换流程

### 4.8 方案八：日志调试启用
**客户端日志配置（log4j2.xml）**：
```xml
<Configuration>
    <Loggers>
        <Logger name="com.clickhouse.client" level="TRACE"/>
        <Logger name="com.clickhouse.jdbc" level="DEBUG"/>
    </Loggers>
</Configuration>
```

---

## 五、进阶排查技巧

### 5.1 服务端错误日志定位
查看 `/var/log/clickhouse-server/clickhouse-server.log`：
```
2024.03.01 12:00:00 Error: SSL_accept failed: error:1407609C:SSL routines:SSL23_GET_CLIENT_HELLO:http request
```

### 5.2 客户端堆栈分析
关键堆栈片段：
```
at com.clickhouse.client.http.HttpConnection.getInputStream(HttpConnection.java:220)
at com.clickhouse.client.ClickHouseClient.read(ClickHouseClient.java:153)
Caused by: javax.net.ssl.SSLException: Unrecognized SSL message, plaintext connection?
```

### 5.3 协议强制验证
```java
// 强制使用TLSv1.3
Properties props = new Properties();
props.setProperty("ssl", "true");
props.setProperty("sslProtocol", "TLSv1.3");
props.setProperty("sslAlgorithm", "SunX509");
```

---

## 六、生产环境最佳实践

### 6.1 SSL配置检查清单
- [ ] 服务端证书链完整
- [ ] 证书未过期
- [ ] 私钥文件权限正确（600）
- [ ] 防火墙开放SSL端口
- [ ] JDBC驱动版本 ≥0.3.2

### 6.2 连接参数推荐配置
```java
String url = "jdbc:ch:https://ch-prod:8443/prod_db"
    + "?socket_timeout=300000"
    + "&compress=true"
    + "&custom_http_headers=X-Client:JavaApp";

Properties props = new Properties();
props.setProperty("ssl", "true");
props.setProperty("sslRootCertificate", "/etc/ssl/certs/ch-ca.pem");
props.setProperty("sslMode", "STRICT");
```

---

## 七、总结与延伸
通过本文的排查方案，可以系统解决 SSL 协议不匹配问题。关键要点：
1. **协议一致性**：确保客户端与服务端使用相同的加密策略
2. **证书信任链**：正确处理自签名证书
3. **中间件透明性**：代理配置需正确转发请求
4. **日志分析**：充分利用调试日志定位问题

延伸阅读建议：
- [ClickHouse SSL 官方文档](https://clickhouse.com/docs/en/operations/ssl)
- [Java 安全套接字编程指南](https://docs.oracle.com/javase/8/docs/technotes/guides/security/jsse/JSSERefGuide.html)
