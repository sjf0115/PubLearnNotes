https://mp.weixin.qq.com/s/nWZY24D60V2BwlLLDxipAg

https://mp.weixin.qq.com/s/x4AhF6bAz6hDMpVfHZylQg

https://github.com/alibaba/druid/wiki/Druid%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%BB%8B%E7%BB%8D




Druid简介

Druid连接池是阿里巴巴开源的数据库连接池项目，为监控而生，内置强大的监控功能，且监控特性不影响性能。Druid连接池功能强大，性能优越，使用占比高，是一款优秀的数据库连接池。Druid连接池的主要特点包括：高性能： Druid连接池采用了一系列性能优化策略，包括预先创建连接、连接池复用、有效的连接验证等，以提供高效的数据库连接获取和释放操作。可靠性： Druid连接池提供了多种故障处理机制，可以有效地应对各种异常情况，确保数据库连接的可靠性。可管理性： Druid连接池提供了丰富的监控和统计功能，可以实时监控连接池的状态、活动连接数、请求频率、SQL执行情况等，方便用户进行管理和优化。安全性： Druid连接池内置了防火墙功能，可以有效地防止SQL注入攻击，并提供审计功能，可以帮助用户追踪数据库操作行为。扩展性： Druid连接池支持多种数据库类型，并可以方便地扩展支持新的数据库类型。Druid连接池的使用非常简单，只需几行代码即可配置和使用，是Java应用开发中不可多得的利器。

Druid 是一个开源的数据库连接池实现，它提供了高效的连接管理和丰富的监控功能。以下是如何在 Java 中使用 Druid 作为 MySQL 数据库连接池的详细步骤：

## 1. 添加依赖

首先，你需要在项目中引入 Druid 的依赖。如果你使用的是 Maven 项目，可以在 pom.xml 文件中添加以下依赖：
```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>druid</artifactId>
    <version>1.2.4</version> <!-- 请使用最新版本 -->
</dependency>

<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.26</version> <!-- 请使用最新版本 -->
</dependency>
```

## 2. 配置 Druid

Druid 支持通过编程方式或配置文件方式进行配置。以下是这两种方式的详细介绍：

### 2.1 编程方式配置
```java
import com.alibaba.druid.pool.DruidDataSource;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;

public class DruidConfigExample {
    public static void main(String[] args) {
        // 创建 Druid 连接池对象
        DruidDataSource dataSource = new DruidDataSource();

        // 配置数据库连接参数
        dataSource.setUrl("jdbc:mysql://localhost:3306/mydb?useSSL=false&serverTimezone=UTC");
        dataSource.setUsername("root");
        dataSource.setPassword("your_password");

        // 配置连接池参数
        dataSource.setInitialSize(5); // 初始化连接数
        dataSource.setMinIdle(5);     // 最小空闲连接数
        dataSource.setMaxActive(20);  // 最大活跃连接数
        dataSource.setMaxWait(60000); // 获取连接的最大等待时间（毫秒）

        // 其他可选配置
        dataSource.setTimeBetweenEvictionRunsMillis(60000); // 连接池检查连接的间隔时间
        dataSource.setMinEvictableIdleTimeMillis(300000);  // 连接池中连接空闲的最小时间
        dataSource.setValidationQuery("SELECT 1");         // 验证连接是否有效的 SQL 语句
        dataSource.setTestWhileIdle(true);                 // 空闲时是否进行连接的验证

        // 使用连接池对象进行数据库操作
        try (Connection connection = dataSource.getConnection()) {
            // 这里执行你的数据库操作
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            // 关闭连接池
            ((DruidDataSource) dataSource).close();
        }
    }
}
```

### 2.2 配置文件方式配置
首先，创建一个 druid.properties 文件，并添加以下配置：

properties
Copy Code
# 设置数据库连接参数
url=jdbc:mysql://localhost:3306/mydb?useSSL=false&serverTimezone=UTC
username=root
password=your_password

# 配置连接池参数
initialSize=5
minIdle=5
maxActive=20
maxWait=60000

# 其他可选配置
timeBetweenEvictionRunsMillis=60000
minEvictableIdleTimeMillis=300000
validationQuery=SELECT 1
testWhileIdle=true
然后，在 Java 代码中加载并使用这个配置文件：

java
Copy Code
import com.alibaba.druid.pool.DruidDataSourceFactory;

import javax.sql.DataSource;
import java.io.IOException;
import java.io.InputStream;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.Properties;

public class DruidConfigExample {
    public static void main(String[] args) {
        Properties properties = new Properties();

        try (InputStream inputStream = DruidConfigExample.class.getClassLoader().getResourceAsStream("druid.properties")) {
            properties.load(inputStream);

            // 创建 Druid 连接池对象
            DataSource dataSource = DruidDataSourceFactory.createDataSource(properties);

            // 使用连接池对象进行数据库操作
            try (Connection connection = dataSource.getConnection()) {
                // 这里执行你的数据库操作
            } catch (SQLException e) {
                e.printStackTrace();
            } finally {
                // 关闭连接池
                ((DruidDataSource) dataSource).close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
3. 监控和诊断
Druid 提供了内置的监控页面，可以通过配置来启用。以下是一个简单的配置示例：

java
Copy Code
import com.alibaba.druid.filter.Filter;
import com.alibaba.druid.filter.stat.StatFilter;
import com.alibaba.druid.support.http.StatViewServlet;
import com.alibaba.druid.wall.WallFilter;
import com.alibaba.druid.wall.WallConfig;
import org.springframework.boot.web.servlet.ServletRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;
import java.util.HashMap;
import java.util.Map;

@Configuration
public class DruidConfig {
    @Bean
    public DataSource dataSource() {
        // 省略了部分代码，与前面的示例类似
        // ...

        // 配置监控
        StatFilter statFilter = new StatFilter();
        statFilter.setSlowSqlMillis(1000);
        statFilter.setLogSlowSql(true);
        statFilter.setMergeSql(true);

        WallFilter wallFilter = new WallFilter();
        WallConfig config = new WallConfig();
        config.setSelectAllow(false);
        config.setUpdateAllow(false);
        config.setInsertAllow(false);
        config.setDeleteAllow(false);
        wallFilter.setConfig(config);

        // 添加过滤器
        Map<String, Filter> filters = new HashMap<>();
        filters.put("stat", statFilter);
        filters.put("wall", wallFilter);
        dataSource.setProxyFilters(filters.values());

        return dataSource;
    }

    @Bean
    public ServletRegistrationBean<StatViewServlet> druidStatViewServlet() {
        ServletRegistrationBean<StatViewServlet> bean = new ServletRegistrationBean<>(new StatViewServlet(), "/druid/*");
        Map<String, String> initParams = new HashMap<>();
        initParams.put("loginUsername", "admin");
        initParams.put("loginPassword", "admin");
        initParams.put("allow", ""); // 允许访问的 IP 地址，为空则允许所有
        initParams.put("deny", ""); // 拒绝访问的 IP 地址，为空则允许所有
        bean.setInitParameters(initParams);
        return bean;
    }
}
在 application.properties 或 application.yml 文件中，确保启用了 Druid 的监控功能：

properties
Copy Code
spring.datasource.druid.stat-view-servlet.enabled=true
配置完成后，通过访问 /druid 路径，你可以查看连接池的实时监控数据。

注意事项
‌连接池参数设置‌：根据应用的实际负载情况合理设置连接池参数，如初始化连接数、最小空闲连接数、最大活跃连接数等。
‌连接泄露‌：确保所有数据库操作都正确释放连接，可以使用 try-with-resources 语句来自动管理资源。
‌定期监控‌：定期监控连接池的状态，包括连接的使用率、等待时间等，并根据监控数据调整连接池参数。
通过以上步骤，你可以在 Java 项目中使用 Druid 作为 MySQL 数据库连接池，从而提高数据库访问的效率和稳定性。
