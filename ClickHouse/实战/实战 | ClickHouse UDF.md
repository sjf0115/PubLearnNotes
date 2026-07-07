ClickHouse 虽然拥有丰富的内置函数库，但面对复杂的业务逻辑（如自定义加解密、地理围栏计算、复杂文本解析等），内置函数往往无法满足需求。ClickHouse 提供了 **Executable UDF（User Defined Function）** 机制，允许通过外部可执行程序扩展 SQL 函数能力。本文将详细介绍如何基于 Java 实现 ClickHouse 自定义 UDF，从原理到实战，帮助你在生产环境中落地 Java UDF。

## 1. ClickHouse UDF 类型概览

ClickHouse 目前支持三种 UDF 类型：

| UDF 类型 | 执行方式 | 适用场景 | 性能特征 |
|---------|---------|---------|---------|
| **SQL UDF** | `CREATE FUNCTION` 内联 SQL | 复用 SQL 表达式逻辑 | 零开销，内联展开 |
| **Executable UDF** | 外部进程，STDIN/STDOUT 通信 | 复杂算法、已有代码集成 | 进程调用有一定开销 |
| **WebAssembly UDF** | WASM 沙箱内执行（实验性） | 高性能自定义算法 | 低开销，沙箱隔离 |

其中 **Executable UDF** 是最灵活的方式，支持任何可执行程序（Python、Go、Java、Rust、Shell 等），也是本文的重点。

## 2. Executable UDF 工作原理

Executable UDF 的核心工作流程如下：

```
┌──────────────────┐     STDIN (TabSeparated)     ┌──────────────────┐
│                  │  ──────────────────────────►  │                  │
│   ClickHouse     │                              │   外部程序        │
│   Server         │  ◄──────────────────────────  │   (Java)         │
│                  │     STDOUT (TabSeparated)     │                  │
└──────────────────┘                              └──────────────────┘
```

**执行流程：**
1. ClickHouse 将函数参数按指定格式（如 `TabSeparated`）通过 **STDIN** 发送给外部进程
2. 外部进程逐行读取输入数据，执行计算逻辑
3. 外部进程将计算结果按相同格式通过 **STDOUT** 返回给 ClickHouse
4. ClickHouse 收集结果并继续查询执行

**两种执行模式：**

- **`executable`**：每个数据块启动一个新进程，处理完即退出。适合启动开销低的脚本语言。
- **`executable_pool`**：维护一个常驻进程池，复用进程处理多次请求。**强烈推荐用于 Java**，避免 JVM 反复启动的巨大开销。

## 3. 为什么选择 Java 实现 UDF

选择 Java 实现 UDF 的场景：

- **复用已有 Java 库**：如 IP 地理位置解析（GeoIP2）、加解密（Bouncy Castle）、NLP 处理等
- **复杂业务逻辑**：多步骤计算、状态机、规则引擎等
- **团队技术栈**：后端团队以 Java 为主，便于维护
- **类型安全与性能**：Java 的 JIT 编译在长时间运行的进程池模式下有显著性能优势

> **注意**：Java 的 JVM 启动开销较大（通常需要数百毫秒），因此 **必须使用 `executable_pool` 模式**，避免每次查询都启动新 JVM。

## 4. 环境准备

### 4.1 ClickHouse 服务端配置

首先确认 ClickHouse 配置中的两个关键路径：

```xml
<!-- /etc/clickhouse-server/config.xml -->
<clickhouse>
    <!-- UDF 配置文件路径（支持通配符，自动加载所有匹配文件） -->
    <user_defined_executable_functions_config>
        /etc/clickhouse-server/custom_functions/*_function.xml
    </user_defined_executable_functions_config>

    <!-- 外部脚本/程序存放路径 -->
    <user_scripts_path>/var/lib/clickhouse/user_scripts/</user_scripts_path>
</clickhouse>
```

- **`user_defined_executable_functions_config`**：UDF 的 XML 配置文件存放位置
- **`user_scripts_path`**：UDF 可执行文件的存放目录（默认 `/var/lib/clickhouse/user_scripts/`）

### 4.2 Java 环境

确保 ClickHouse 所在服务器已安装 JDK：

```bash
# 验证 Java 环境
java -version

# 确认 JAVA_HOME
echo $JAVA_HOME
```

> 推荐使用 JDK 11 或更高版本，以获得更好的启动性能和内存管理。

## 5. 实战一：简单标量 UDF（字符串脱敏）

我们从一个简单的示例开始 —— 实现一个手机号脱敏函数 `mask_phone`，将手机号中间四位替换为 `****`。

### 5.1 Java 实现

创建 Maven 项目，编写 UDF 主类：

```java
package com.example.clickhouse.udf;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;

/**
* 手机号脱敏 UDF
* 输入：手机号字符串（TabSeparated）
* 输出：脱敏后的手机号
*/
public class MaskPhoneUDF {

    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        PrintWriter writer = new PrintWriter(System.out, false);

        String line;
        while ((line = reader.readLine()) != null) {
            String result = maskPhone(line.trim());
            writer.println(result);
            writer.flush();
        }

        writer.close();
        reader.close();
    }

    private static String maskPhone(String phone) {
        if (phone == null || phone.length() != 11) {
            return phone;
        }
        return phone.substring(0, 3) + "****" + phone.substring(7);
    }
}
```

**关键设计要点：**

1. **从 STDIN 逐行读取**：每行对应一个函数调用的输入参数
2. **向 STDOUT 逐行输出**：每行对应一个返回值
3. **及时 flush**：确保 ClickHouse 能及时收到结果，避免死锁
4. **无限循环读取**：在 `executable_pool` 模式下，进程常驻，持续处理数据

### 5.2 打包为 Fat JAR

使用 Maven Shade Plugin 打包为一个独立的 Fat JAR：

```xml
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>clickhouse-udf</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.5.1</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                        <configuration>
                            <transformers>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>com.example.clickhouse.udf.MaskPhoneUDF</mainClass>
                                </transformer>
                            </transformers>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

打包：

```bash
mvn clean package -DskipTests
```

### 5.3 部署到 ClickHouse

将 JAR 和启动脚本部署到 `user_scripts` 目录：

```bash
# 将 JAR 包复制到 user_scripts 目录
cp target/clickhouse-udf-1.0.0.jar /var/lib/clickhouse/user_scripts/

# 创建启动脚本
cat > /var/lib/clickhouse/user_scripts/mask_phone.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
exec java -jar "$SCRIPT_DIR/clickhouse-udf-1.0.0.jar"
EOF

# 设置执行权限
chmod +x /var/lib/clickhouse/user_scripts/mask_phone.sh
```

> 为什么需要 Shell 启动脚本？因为 ClickHouse 的 `command` 配置项直接执行文件时，`execute_direct=1` 模式下需要可执行文件。通过 Shell 脚本包装 `java -jar` 命令是最简洁的方式。

### 5.4 配置 UDF

创建 UDF 配置文件：

```xml
<!-- /etc/clickhouse-server/custom_functions/mask_phone_function.xml -->
<functions>
    <function>
        <type>executable_pool</type>
        <name>mask_phone</name>
        <return_type>String</return_type>
        <argument>
            <type>String</type>
            <name>phone</name>
        </argument>
        <format>TabSeparated</format>
        <command>mask_phone.sh</command>
        <pool_size>4</pool_size>
        <max_command_execution_time>30</max_command_execution_time>
        <send_chunk_header>false</send_chunk_header>
    </function>
</functions>
```

**配置参数说明：**

| 参数 | 说明 |
|-----|------|
| `type` | 设为 `executable_pool`，维护常驻进程池 |
| `name` | SQL 中调用的函数名 |
| `return_type` | 返回值类型 |
| `argument` | 参数定义（支持多个） |
| `format` | 数据交换格式，`TabSeparated` 最常用 |
| `command` | user_scripts 目录下的可执行文件名 |
| `pool_size` | 进程池大小，建议设为 CPU 核数 |
| `max_command_execution_time` | 单次执行超时时间（秒） |

### 5.5 验证 UDF

配置完成后，ClickHouse 会自动加载（也可通过 `SYSTEM RELOAD FUNCTIONS` 触发重新加载）：

```sql
-- 验证函数已注册
SELECT name, origin FROM system.functions WHERE name = 'mask_phone';

-- 测试调用
SELECT mask_phone('13812345678');
-- 结果：138****5678

-- 在查询中使用
SELECT
    user_id,
    mask_phone(phone) AS masked_phone
FROM user_info
LIMIT 10;
```

## 6. 实战二：多参数 UDF（坐标距离计算）

实现一个计算两个经纬度坐标之间距离的函数 `geo_distance`。

### 6.1 Java 实现

```java
package com.example.clickhouse.udf;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;

/**
* 地理距离计算 UDF（Haversine 公式）
* 输入：lat1\tlon1\tlat2\tlon2（四列 TabSeparated）
* 输出：距离（米）
*/
public class GeoDistanceUDF {

    private static final double EARTH_RADIUS = 6371000; // 地球半径（米）

    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        PrintWriter writer = new PrintWriter(System.out, false);

        String line;
        while ((line = reader.readLine()) != null) {
            String[] parts = line.split("\t");
            if (parts.length == 4) {
                double lat1 = Double.parseDouble(parts[0].trim());
                double lon1 = Double.parseDouble(parts[1].trim());
                double lat2 = Double.parseDouble(parts[2].trim());
                double lon2 = Double.parseDouble(parts[3].trim());

                double distance = haversine(lat1, lon1, lat2, lon2);
                writer.printf("%.2f%n", distance);
            } else {
                writer.println("0.00");
            }
            writer.flush();
        }

        writer.close();
    }

    private static double haversine(double lat1, double lon1, double lat2, double lon2) {
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                 + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))
                 * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return EARTH_RADIUS * c;
    }
}
```

### 6.2 UDF 配置

```xml
<!-- /etc/clickhouse-server/custom_functions/geo_distance_function.xml -->
<functions>
    <function>
        <type>executable_pool</type>
        <name>geo_distance</name>
        <return_type>Float64</return_type>
        <argument>
            <type>Float64</type>
            <name>lat1</name>
        </argument>
        <argument>
            <type>Float64</type>
            <name>lon1</name>
        </argument>
        <argument>
            <type>Float64</type>
            <name>lat2</name>
        </argument>
        <argument>
            <type>Float64</type>
            <name>lon2</name>
        </argument>
        <format>TabSeparated</format>
        <command>geo_distance.sh</command>
        <pool_size>8</pool_size>
        <max_command_execution_time>30</max_command_execution_time>
    </function>
</functions>
```

### 6.3 使用示例

```sql
-- 计算北京到上海的直线距离
SELECT geo_distance(39.9042, 116.4074, 31.2304, 121.4737) AS distance_meters;
-- 结果约：1067975.55（约 1068 公里）

-- 在业务查询中使用：查找 5 公里内的门店
SELECT
    store_name,
    geo_distance(user_lat, user_lon, store_lat, store_lon) AS distance
FROM stores
WHERE geo_distance(user_lat, user_lon, store_lat, store_lon) < 5000
ORDER BY distance;
```

## 7. 实战三：使用 JSONEachRow 格式

对于复杂参数和返回值，`JSONEachRow` 格式更加直观和灵活。

### 7.1 Java 实现（JSON 格式）

使用 Jackson 库解析 JSON：

```java
package com.example.clickhouse.udf;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;

/**
* 身份证信息解析 UDF（JSONEachRow 格式）
* 输入 JSON：{"id_card": "110105199003071234"}
* 输出 JSON：{"province": "北京市", "birthday": "1990-03-07", "gender": "男"}
*/
public class ParseIdCardUDF {

    private static final ObjectMapper mapper = new ObjectMapper();

    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        PrintWriter writer = new PrintWriter(System.out, false);

        String line;
        while ((line = reader.readLine()) != null) {
            try {
                JsonNode input = mapper.readTree(line);
                String idCard = input.get("id_card").asText();

                ObjectNode result = mapper.createObjectNode();
                result.put("province", extractProvince(idCard));
                result.put("birthday", extractBirthday(idCard));
                result.put("gender", extractGender(idCard));

                writer.println(mapper.writeValueAsString(result));
            } catch (Exception e) {
                ObjectNode errorResult = mapper.createObjectNode();
                errorResult.put("province", "未知");
                errorResult.put("birthday", "未知");
                errorResult.put("gender", "未知");
                writer.println(mapper.writeValueAsString(errorResult));
            }
            writer.flush();
        }

        writer.close();
    }

    private static String extractProvince(String idCard) {
        String code = idCard.substring(0, 2);
        switch (code) {
            case "11": return "北京市";
            case "12": return "天津市";
            case "31": return "上海市";
            case "44": return "广东省";
            case "33": return "浙江省";
            // ... 更多省份映射
            default: return "未知";
        }
    }

    private static String extractBirthday(String idCard) {
        String year = idCard.substring(6, 10);
        String month = idCard.substring(10, 12);
        String day = idCard.substring(12, 14);
        return year + "-" + month + "-" + day;
    }

    private static String extractGender(String idCard) {
        int genderCode = Integer.parseInt(idCard.substring(16, 17));
        return genderCode % 2 == 0 ? "女" : "男";
    }
}
```

### 7.2 UDF 配置（多返回列）

当 UDF 返回多个字段时，结合 `JSONEachRow` 格式和 `return_name` 来指定返回字段名：

```xml
<!-- /etc/clickhouse-server/custom_functions/parse_idcard_function.xml -->
<functions>
    <function>
        <type>executable_pool</type>
        <name>parse_idcard_province</name>
        <return_type>String</return_type>
        <return_name>province</return_name>
        <argument>
            <type>String</type>
            <name>id_card</name>
        </argument>
        <format>JSONEachRow</format>
        <command>parse_idcard.sh</command>
        <pool_size>4</pool_size>
    </function>

    <function>
        <type>executable_pool</type>
        <name>parse_idcard_birthday</name>
        <return_type>String</return_type>
        <return_name>birthday</return_name>
        <argument>
            <type>String</type>
            <name>id_card</name>
        </argument>
        <format>JSONEachRow</format>
        <command>parse_idcard.sh</command>
        <pool_size>4</pool_size>
    </function>

    <function>
        <type>executable_pool</type>
        <name>parse_idcard_gender</name>
        <return_type>String</return_type>
        <return_name>gender</return_name>
        <argument>
            <type>String</type>
            <name>id_card</name>
        </argument>
        <format>JSONEachRow</format>
        <command>parse_idcard.sh</command>
        <pool_size>4</pool_size>
    </function>
</functions>
```

> **提示**：ClickHouse 的 Executable UDF 目前只支持**单值返回**（一个 `return_type`）。如果需要解析出多个字段，需注册多个函数，每个函数对应一个 `return_name`，它们可以共享同一个脚本。

### 7.3 使用示例

```sql
SELECT
    parse_idcard_province('110105199003071234') AS province,
    parse_idcard_birthday('110105199003071234') AS birthday,
    parse_idcard_gender('110105199003071234') AS gender;

-- 结果：
-- ┌─province─┬─birthday───┬─gender─┐
-- │ 北京市    │ 1990-03-07 │ 男     │
-- └──────────┴────────────┴────────┘
```

## 8. 实战四：带外部依赖的 UDF（IP 地理位置解析）

这是一个更贴近生产的示例 —— 使用 MaxMind GeoIP2 库解析 IP 地址的地理位置。

### 8.1 项目依赖

```xml
<dependencies>
    <!-- MaxMind GeoIP2 -->
    <dependency>
        <groupId>com.maxmind.geoip2</groupId>
        <artifactId>geoip2</artifactId>
        <version>4.2.0</version>
    </dependency>
</dependencies>
```

### 8.2 Java 实现

```java
package com.example.clickhouse.udf;

import com.maxmind.geoip2.DatabaseReader;
import com.maxmind.geoip2.model.CityResponse;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.InetAddress;

/**
* IP 地理位置解析 UDF
* 输入：IP 地址字符串
* 输出：城市名（TabSeparated）
*/
public class IpGeoCityUDF {

    private static DatabaseReader dbReader;

    public static void main(String[] args) throws Exception {
        // 初始化 GeoIP2 数据库（只加载一次，常驻内存）
        String dbPath = System.getenv("GEOIP_DB_PATH");
        if (dbPath == null || dbPath.isEmpty()) {
            dbPath = "/var/lib/clickhouse/user_scripts/GeoLite2-City.mmdb";
        }
        dbReader = new DatabaseReader.Builder(new File(dbPath)).build();

        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        PrintWriter writer = new PrintWriter(System.out, false);

        String line;
        while ((line = reader.readLine()) != null) {
            String ip = line.trim();
            String city = resolveCity(ip);
            writer.println(city);
            writer.flush();
        }

        writer.close();
        dbReader.close();
    }

    private static String resolveCity(String ip) {
        try {
            InetAddress address = InetAddress.getByName(ip);
            CityResponse response = dbReader.city(address);
            String city = response.getCity().getName();
            return city != null ? city : "Unknown";
        } catch (Exception e) {
            return "Unknown";
        }
    }
}
```

**优势**：`executable_pool` 模式下，GeoIP2 数据库只加载一次，后续每次查询直接复用内存中的数据库实例，性能极高。

### 8.3 启动脚本（支持环境变量）

```bash
#!/bin/bash
# /var/lib/clickhouse/user_scripts/ip_geo_city.sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
export GEOIP_DB_PATH="$SCRIPT_DIR/GeoLite2-City.mmdb"

exec java \
    -Xms128m -Xmx256m \
    -XX:+UseG1GC \
    -jar "$SCRIPT_DIR/clickhouse-udf-1.0.0.jar" \
    ip_geo_city
```

> **技巧**：通过命令行参数或环境变量区分不同的 UDF 入口，可以将多个 UDF 打包到同一个 JAR 中。

### 8.4 统一入口的多 UDF 设计

如果项目中有多个 UDF，可以设计一个统一入口类：

```java
package com.example.clickhouse.udf;

public class UDFRouter {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            System.err.println("Usage: java -jar udf.jar <function_name>");
            System.exit(1);
        }

        String functionName = args[0];
        switch (functionName) {
            case "mask_phone":
                MaskPhoneUDF.main(new String[]{});
                break;
            case "geo_distance":
                GeoDistanceUDF.main(new String[]{});
                break;
            case "ip_geo_city":
                IpGeoCityUDF.main(new String[]{});
                break;
            default:
                System.err.println("Unknown function: " + functionName);
                System.exit(1);
        }
    }
}
```

对应的启动脚本只需修改参数：

```bash
#!/bin/bash
# mask_phone.sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
exec java -jar "$SCRIPT_DIR/clickhouse-udf-1.0.0.jar" mask_phone
```

## 9. send_chunk_header 批量处理模式

当处理大量数据时，启用 `send_chunk_header` 可以让 Java 程序知道每个数据块的行数，从而进行更高效的批量处理。

### 9.1 协议说明

启用 `send_chunk_header` 后，ClickHouse 发送数据的格式变为：

```
<row_count>\n          ← 第一行：本次 chunk 的行数
<row_1>\n              ← 第 1 行数据
<row_2>\n              ← 第 2 行数据
...
<row_N>\n              ← 第 N 行数据
<row_count>\n          ← 下一个 chunk 的行数
...
```

### 9.2 Java 实现（支持 chunk header）

```java
package com.example.clickhouse.udf;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;

/**
* 支持 send_chunk_header 的批量处理 UDF
*/
public class BatchProcessUDF {

    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        PrintWriter writer = new PrintWriter(System.out, false);

        String line;
        while ((line = reader.readLine()) != null) {
            // 第一行是 chunk 的行数
            int rowCount = Integer.parseInt(line.trim());

            // 可以预分配资源
            StringBuilder batch = new StringBuilder(rowCount * 64);

            // 读取并处理 rowCount 行数据
            for (int i = 0; i < rowCount; i++) {
                String dataLine = reader.readLine();
                if (dataLine == null) break;

                String result = processRow(dataLine);
                batch.append(result).append('\n');
            }

            // 批量输出结果
            writer.print(batch);
            writer.flush();
        }

        writer.close();
    }

    private static String processRow(String input) {
        // 自定义业务逻辑
        return input.trim().toUpperCase();
    }
}
```

### 9.3 对应 UDF 配置

```xml
<functions>
    <function>
        <type>executable_pool</type>
        <name>batch_upper</name>
        <return_type>String</return_type>
        <argument>
            <type>String</type>
            <name>input</name>
        </argument>
        <format>TabSeparated</format>
        <command>batch_upper.sh</command>
        <pool_size>8</pool_size>
        <send_chunk_header>true</send_chunk_header>
        <max_command_execution_time>60</max_command_execution_time>
    </function>
</functions>
```

## 10. 性能优化最佳实践

### 10.1 JVM 参数调优

根据 UDF 的内存需求调整 JVM 参数：

```bash
#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
exec java \
    -Xms128m \
    -Xmx512m \
    -XX:+UseG1GC \
    -XX:MaxGCPauseMillis=50 \
    -XX:+UseStringDeduplication \
    -Djava.security.egd=file:/dev/./urandom \
    -jar "$SCRIPT_DIR/clickhouse-udf-1.0.0.jar" "$@"
```

### 10.2 pool_size 设置建议

| 场景 | 建议 pool_size | 说明 |
|-----|---------------|------|
| 轻量计算 UDF | CPU 核数 | 如字符串处理、简单运算 |
| I/O 密集型 UDF | CPU 核数 × 2 | 如文件读取、网络请求 |
| 重内存型 UDF | 根据内存限制 | 如 GeoIP 数据库（每个进程加载一份） |
| 查询并发很低 | 2~4 | 节省资源 |

### 10.3 I/O 优化

```java
// 推荐：使用 BufferedReader + PrintWriter，批量 flush
BufferedReader reader = new BufferedReader(
    new InputStreamReader(System.in),
    8192  // 8KB 缓冲区
);
PrintWriter writer = new PrintWriter(
    new java.io.BufferedOutputStream(System.out, 8192),
    false  // 手动 flush，避免每次 println 都 flush
);

// 处理一批数据后统一 flush
for (int i = 0; i < rowCount; i++) {
    String line = reader.readLine();
    writer.println(processRow(line));
}
writer.flush();  // 一次 flush
```

### 10.4 避免常见性能陷阱

| 陷阱 | 问题 | 解决方案 |
|------|------|---------|
| 使用 `executable` 类型 | 每次都启动 JVM，耗时数百毫秒 | 改用 `executable_pool` |
| 每行都 flush | I/O 系统调用过多 | 使用 `send_chunk_header`，按 chunk flush |
| PrintWriter autoFlush=true | 同上 | 设为 false，手动 flush |
| 在循环中创建对象 | GC 压力大 | 提到循环外或使用对象池 |
| 未设置 JVM 内存上限 | 可能 OOM | 通过 -Xmx 限制堆大小 |

## 11. 错误处理与监控

### 11.1 异常处理策略

Java UDF 中的异常处理至关重要，因为任何未捕获的异常都会导致进程退出：

```java
public static void main(String[] args) throws Exception {
    BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
    PrintWriter writer = new PrintWriter(System.out, false);

    // 设置全局异常处理器
    Thread.setDefaultUncaughtExceptionHandler((t, e) -> {
        System.err.println("UDF Fatal Error: " + e.getMessage());
        e.printStackTrace(System.err);
    });

    String line;
    while ((line = reader.readLine()) != null) {
        try {
            String result = processRow(line);
            writer.println(result);
        } catch (Exception e) {
            // 单行处理失败不影响整体
            System.err.println("Error processing: " + line + " -> " + e.getMessage());
            writer.println(getDefaultValue());  // 返回默认值
        }
        writer.flush();
    }

    writer.close();
}
```

### 11.2 日志与 stderr

ClickHouse 可以通过 `stderr_reaction` 配置控制如何处理 UDF 程序的 stderr 输出：

```xml
<function>
    <!-- ... 其他配置 ... -->
    <!-- stderr 处理策略 -->
    <stderr_reaction>log_last</stderr_reaction>
    <!-- 可选值：
         none      - 忽略 stderr
         log       - 实时记录所有 stderr
         log_first - 记录前 4KB stderr（进程退出后）
         log_last  - 记录最后 4KB stderr（进程退出后，默认）
         throw     - stderr 有输出就抛异常
    -->
    <check_exit_code>true</check_exit_code>
</function>
```

### 11.3 健康检查

可以通过系统表监控 UDF 状态：

```sql
-- 查看已注册的 UDF
SELECT
    name,
    origin,
    create_query
FROM system.functions
WHERE origin = 'ExecutableUserDefined';

-- 查看 UDF 详细信息
SELECT *
FROM system.user_defined_functions
WHERE name = 'mask_phone';
```

## 12. Docker 环境下的部署

在 Docker 容器中部署 Java UDF 需要确保 JDK 环境可用：

### 12.1 自定义 Dockerfile

```dockerfile
FROM clickhouse/clickhouse-server:latest

# 安装 JDK
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless && \
    rm -rf /var/lib/apt/lists/*

# 复制 UDF 文件
COPY clickhouse-udf-1.0.0.jar /var/lib/clickhouse/user_scripts/
COPY scripts/*.sh /var/lib/clickhouse/user_scripts/
COPY functions/*.xml /etc/clickhouse-server/custom_functions/

# 设置权限
RUN chmod +x /var/lib/clickhouse/user_scripts/*.sh
```

### 12.2 Docker Compose 配置

```yaml
version: '3.8'
services:
  clickhouse:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - ./data:/var/lib/clickhouse
      - ./config/custom_functions:/etc/clickhouse-server/custom_functions
      - ./user_scripts:/var/lib/clickhouse/user_scripts
    environment:
      - CLICKHOUSE_USER=default
      - CLICKHOUSE_PASSWORD=
```

## 13. 完整项目结构

最终项目的推荐目录结构如下：

```
clickhouse-java-udf/
├── pom.xml
├── src/main/java/com/example/clickhouse/udf/
│   ├── UDFRouter.java              # 统一入口路由
│   ├── MaskPhoneUDF.java           # 手机号脱敏
│   ├── GeoDistanceUDF.java         # 地理距离计算
│   ├── ParseIdCardUDF.java         # 身份证解析
│   ├── IpGeoCityUDF.java           # IP 地理位置
│   └── BatchProcessUDF.java        # 批量处理示例
├── deploy/
│   ├── scripts/                    # Shell 启动脚本
│   │   ├── mask_phone.sh
│   │   ├── geo_distance.sh
│   │   ├── parse_idcard.sh
│   │   └── ip_geo_city.sh
│   ├── functions/                  # UDF XML 配置
│   │   ├── mask_phone_function.xml
│   │   ├── geo_distance_function.xml
│   │   ├── parse_idcard_function.xml
│   │   └── ip_geo_city_function.xml
│   ├── Dockerfile
│   └── docker-compose.yml
└── README.md
```

## 14. 常见问题排查

### 14.1 函数未找到

```
DB::Exception: Unknown function mask_phone
```

**排查步骤：**
1. 检查 XML 配置是否在 `user_defined_executable_functions_config` 指定的路径下
2. 执行 `SYSTEM RELOAD FUNCTIONS` 重新加载
3. 查看 ClickHouse 日志中的加载错误

### 14.2 超时错误

```
DB::Exception: Executable pool max_command_execution_time exceeded
```

**解决方案：**
- 增大 `max_command_execution_time`
- 优化 Java 逻辑或增大 pool_size
- 检查是否存在死锁（未 flush 导致）

### 14.3 进程启动失败

```
DB::Exception: Cannot execute command
```

**排查步骤：**
1. 确认脚本有执行权限：`chmod +x script.sh`
2. 手动运行脚本确认无报错：`echo "test" | ./mask_phone.sh`
3. 确认 Java 在 ClickHouse 运行用户的 PATH 中可用
4. 检查 JAR 包路径是否正确

### 14.4 结果数量不匹配

```
DB::Exception: The result of external function has wrong number of rows
```

**原因**：输入 N 行但输出不是 N 行。必须确保**输入输出行数严格一一对应**。

**解决方案**：确保每行输入都有且仅有一行输出，即使处理出错也要输出默认值。

## 15. 总结

基于 Java 实现 ClickHouse UDF 的核心要点：

1. **必须使用 `executable_pool`**：避免 JVM 重复启动开销
2. **STDIN/STDOUT 协议**：逐行读入参数，逐行输出结果，输入输出行数必须一一对应
3. **Fat JAR + Shell 脚本**：最佳打包部署方式
4. **及时 flush**：避免缓冲导致的超时和死锁
5. **健壮的异常处理**：单行失败不能影响进程，返回默认值继续处理
6. **启用 `send_chunk_header`**：大数据量场景下批量处理更高效
7. **统一入口路由**：多个 UDF 共享一个 JAR 包，通过参数区分

通过 `executable_pool` + Java 的组合，可以将 ClickHouse 的函数能力扩展到几乎任何业务逻辑，同时兼顾了开发效率和运行时性能。
