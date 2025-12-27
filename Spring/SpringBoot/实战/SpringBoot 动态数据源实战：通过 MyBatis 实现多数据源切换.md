在现代微服务架构中，单一应用连接多个数据库的场景越来越常见。例如，电商系统中订单数据和商品数据可能分布在不同的物理数据库上，如何优雅地管理这些数据源并实现透明切换是架构设计的重要课题。本文将详细介绍如何使用 Spring Boot 通过配置多个独立的 MyBatis 框架实例来实现多数据源访问，让订单和商品数据源能够按需切换。

## 1. 项目依赖

首先使用 Spring Initializr 创建项目，需要在 pom.xml 文件中引入如下依赖：
```xml
<!-- SpringBoot工程需要继承的父工程 -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.5</version>
    <relativePath/>
</parent>

<artifactId>spring-boot-simple-dynamic-datasource</artifactId>

<properties>
    <mybatis.spring.version>2.3.2</mybatis.spring.version>
    <druid.spring.version>1.2.27</druid.spring.version>
    <mysql.version>5.1.46</mysql.version>
    <lombok.version>1.18.26</lombok.version>
</properties>

<dependencies>
    <!-- Web开发需要的起步依赖 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- 集成 Mybatis -->
    <dependency>
        <groupId>org.mybatis.spring.boot</groupId>
        <artifactId>mybatis-spring-boot-starter</artifactId>
        <version>${mybatis.spring.version}</version>
    </dependency>

    <!-- 集成 Druid -->
    <dependency>
        <groupId>com.alibaba</groupId>
        <artifactId>druid-spring-boot-starter</artifactId>
        <version>${druid.spring.version}</version>
    </dependency>

    <!-- MySQL 驱动 -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
        <version>${mysql.version}</version>
    </dependency>

    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <version>${lombok.version}</version>
    </dependency>

</dependencies>
```

## 2. 配置文件

在 application.yml 中配置数据库信息，使用 orders 和 goods 两个数据库：
```
server:
  port: 8090

spring:
  datasource:
    # 订单数据源
    order:
      type: com.alibaba.druid.pool.DruidDataSource
      driver-class-name: com.mysql.cj.jdbc.Driver
      url: jdbc:mysql://localhost:3306/orders?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true
      username: root
      password: root

    # 商品数据源
    goods:
      type: com.alibaba.druid.pool.DruidDataSource
      driver-class-name: com.mysql.cj.jdbc.Driver
      url: jdbc:mysql://localhost:3306/goods?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true
      username: root
      password: root
```

## 3. 数据源配置

### 3.1 数据源类型枚举

```java
public enum DataSourceType {
    /**
     * 订单数据源
     */
    ORDER("order"),

    /**
     * 商品数据源
     */
    GOODS("goods");

    private final String name;

    DataSourceType(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    /**
     * 根据名称获取枚举
     */
    public static DataSourceType fromName(String name) {
        for (DataSourceType type : DataSourceType.values()) {
            if (type.name.equalsIgnoreCase(name)) {
                return type;
            }
        }
        throw new IllegalArgumentException("未知的数据源类型: " + name);
    }
}
```

### 3.2 数据源配置类

通过配置多个独立的 MyBatis 框架实例来实现多数据源访问，那就需要为每个数据源配置单独的配置类。

#### 3.2.1 订单数据源

为订单数据源配置 OrderDataSourceConfig 配置类：
```java
@Configuration
@MapperScan(
        // 包路径下扫描 Mapper 接口
        basePackages = "com.spring.example.mapper.order",
        // 使用哪个 SqlSessionFactory
        sqlSessionFactoryRef = "orderSqlSessionFactory"
)
public class OrderDataSourceConfig {
    // 订单数据源
    @Bean
    @ConfigurationProperties(prefix = "spring.datasource.order")
    public DataSource orderDataSource() {
        // 底层会自动拿到 spring.datasource.order 中的配置创建一个 DruidDataSource
        return DruidDataSourceBuilder.create().build();
    }

    @Bean(name = "orderSqlSessionFactory")
    @Primary
    public SqlSessionFactory orderSqlSessionFactory() throws Exception {
        final SqlSessionFactoryBean sessionFactory = new SqlSessionFactoryBean();
        // 设置数据源
        sessionFactory.setDataSource(orderDataSource());
        // 加载XML映射文件
        sessionFactory.setMapperLocations(
                new PathMatchingResourcePatternResolver()
                        .getResources("classpath:mapper/order/*.xml"));

        // 可选但建议的配置
        sessionFactory.setTypeAliasesPackage("com.spring.example.bean.order");
        // 可选：配置驼峰命名
        org.apache.ibatis.session.Configuration configuration =
                new org.apache.ibatis.session.Configuration();
        configuration.setMapUnderscoreToCamelCase(true);
        sessionFactory.setConfiguration(configuration);

        return sessionFactory.getObject();
    }
}
```
`@MapperScan` 告诉 Spring 在指定的包路径下扫描 Mapper 接口（即 DAO 接口），并将这些接口注册为 MyBatis 的 Mapper。同时，通过 sqlSessionFactoryRef 属性指定这些 Mapper 接口使用哪个 SqlSessionFactory 来创建代理对象。

因为 `@MapperScan` 只是将 Mapper 接口注册到 Spring 容器，并指定使用哪个 SqlSessionFactory，但并没有告诉 SqlSessionFactory 去哪里加载 XML 映射文件（如果你使用 XML 方式定义 SQL 映射的话）。

`setMapperLocations` 告诉 MyBatis 去哪里找 XML 映射文件，并将 XML 中的 SQL 与方法绑定。如果你在 Mapper 接口中使用了注解来定义 SQL，那么可以不用设置 XML 映射文件的位置。但如果你使用了 XML 文件，则必须设置。

#### 3.2.2 商品数据源

同理为商品数据源配置 GoodsDataSourceConfig 配置类：
```java
@Configuration
@MapperScan(basePackages = "com.spring.example.mapper.goods",
        sqlSessionFactoryRef = "goodsSqlSessionFactory")
public class GoodsDataSourceConfig {
    // 商品数据源
    @Bean
    @ConfigurationProperties(prefix = "spring.datasource.goods")
    public DataSource goodsDataSource() {
        // 底层会自动拿到 spring.datasource.order 中的配置创建一个 DruidDataSource
        return DruidDataSourceBuilder.create().build();
    }

    @Bean
    public SqlSessionFactory goodsSqlSessionFactory(@Qualifier("goodsDataSource") DataSource goodsDataSource) throws Exception {
        final SqlSessionFactoryBean sessionFactory = new SqlSessionFactoryBean();
        sessionFactory.setDataSource(goodsDataSource);
        sessionFactory.setMapperLocations(
                new PathMatchingResourcePatternResolver()
                        .getResources("classpath:mapper/goods/*.xml"));
        return sessionFactory.getObject();
    }
}
```

## 4. 实体类

在 `com.spring.example.bean` 包路径下定义 POJO 实体，在这创建两个实体分别对应两个数据库实体对象：
```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Goods {
    private Long id;
    private String name;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Order {
    private Long id;
    private double price;
}
```

## 5. MyBatis 配置文件

### 5.1 创建 Mapper XML 定义映射配置

分别在 `resources/mapper/goods` 和 `resources/mapper/order` 目录下创建 GoodsMapper.xml 和 OrderMapper.xml 文件。

GoodsMapper.xml 文件如下所示：
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper
        PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<!-- namespace 命名空间 -->
<mapper namespace="com.spring.example.mapper.goods.GoodsMapper">

    <resultMap id="BaseResultMap" type="com.spring.example.bean.Goods">
        <id column="id" jdbcType="BIGINT" property="id" />
        <result column="name" jdbcType="VARCHAR" property="name" />
    </resultMap>

    <sql id="Base_Column_List">
        id, name
    </sql>

    <!-- 查询所有的商品 -->
    <select id="selectAll" resultMap="BaseResultMap">
        SELECT
        <include refid="Base_Column_List" />
        FROM tb_goods
    </select>
</mapper>
```
OrderMapper.xml 文件如下所示：
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper
        PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<!-- namespace 命名空间 -->
<mapper namespace="com.spring.example.mapper.order.OrderMapper">

    <resultMap id="BaseResultMap" type="com.spring.example.bean.Order">
        <id column="id" jdbcType="BIGINT" property="id" />
        <result column="price" jdbcType="DOUBLE" property="price" />
    </resultMap>

    <sql id="Base_Column_List">
        id, price
    </sql>

    <!-- 查询所有的订单 -->
    <select id="selectAll" resultMap="BaseResultMap">
        SELECT
        <include refid="Base_Column_List" />
        FROM tb_order
    </select>
</mapper>
```
Mapper 映射文件中定义了 SQL 查询语句实现与数据库的交互，主要目的是实现 SQL 的统一管理。一个 SQL 语句既可以通过 XML 定义，也可以通过注解定义。因为 MyBatis 提供的所有特性都可以利用基于 XML 的映射语言来实现，在这我们采用 XML 来定义语句。

#### 5.2 定义 Mapper 数据层接口

分别在 `com.spring.example.mapper.goods` 和 `com.spring.example.mapper.order` 包路径下创建 GoodsMapper 和 OrderMapper 类：
```java
@Mapper
public interface GoodsMapper {
    List<Goods> selectAll();
}

@Mapper
public interface OrderMapper {
    List<Order> selectAll();
}
```

## 6. Service层实现

Service 层 GoodsService 和 OrderService 中提供 getList 方法来获取所有的商品和订单：
```java
@Service
public class GoodsService {
    @Autowired
    private GoodsMapper goodsMapper;

    /**
     * 获取商品列表
     * @return
     */
    public List<Goods> getList() {
        return goodsMapper.selectAll();
    }
}

@Service
public class OrderService {
    @Resource
    private OrderMapper orderMapper;

    /**
     * 获取订单列表
     * @return
     */
    public List<Order> getList() {
        List<Order> orders = orderMapper.selectAll();
        return orders;
    }
}
```

## 7. Controller层实现

Controller 层 GoodsController 和 OrderController 中提供 getList 方法来获取所有的商品和订单：
```java
@Slf4j
@RestController
@RequestMapping(value = "/goods", produces = MediaType.APPLICATION_JSON_VALUE)
public class GoodsController {
    @Autowired
    private GoodsService goodsService;

    @GetMapping(value = "/list")
    public List<Goods> getList() {
        return goodsService.getList();
    }
}

@Slf4j
@RestController
@RequestMapping(value = "/order", produces = MediaType.APPLICATION_JSON_VALUE)
public class OrderController {
    @Autowired
    private OrderService orderService;

    @GetMapping(value = "/list")
    public List<Order> getList() {
        List<Order> orders = orderService.getList();
        return orders;
    }
}
```

## 8. 效果

请求 `http://localhost:8090/goods/list` 接口获取所有的商品：
```json
[
  {
    "id": 1,
    "name": "花"
  },
  {
    "id": 2,
    "name": "剃须刀"
  },
  {
    "id": 3,
    "name": "袜子"
  },
  {
    "id": 4,
    "name": "笔记本"
  }
]
```
请求 `http://localhost:8090/order/list` 接口获取所有的订单：
```json
[
  {
    "id": 1,
    "price": 18.8
  },
  {
    "id": 2,
    "price": 201
  },
  {
    "id": 3,
    "price": 25.3
  },
  {
    "id": 4,
    "price": 11
  }
]
```

> [完整代码实现](https://github.com/sjf0115/spring-example/tree/main/spring-boot-dynamic-datasource-mybatis)
