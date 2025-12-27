在现代微服务架构中，单一应用连接多个数据库的场景越来越常见。例如，电商系统中订单数据和商品数据可能分布在不同的物理数据库上，如何优雅地管理这些数据源并实现透明切换是架构设计的重要课题。本文将详细介绍如何使用 Spring Boot 通过 AOP + 注解方式实现多数据源动态切换，让订单和商品数据源能够按需切换。


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

    <!-- AOP -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-aop</artifactId>
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

# MyBatis 配置
mybatis:
  # 指定 mapper.xml 文件路径
  mapper-locations: classpath:mapper/*.xml
  # 指定实体类包路径 xxxMapper.xml 不用指定全限定名
  type-aliases-package: com.spring.example.bean
  configuration:
    # 开启驼峰命名转换
    map-underscore-to-camel-case: true
```

## 3. 创建动态数据源

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

### 3.2 数据源上下文持有器

动态数据源上下文持有器 DataSourceContextHolder 使用 ThreadLocal 保证线程安全。基于 ThreadLocal 线程局部变量对象，创建一个用于缓存数据源类型的类，后续通过这个类来动态切换要使用的数据源：
```java
public class DataSourceContextHolder {
    private static final ThreadLocal<DataSourceType> DATASOURCE_HOLDER = new ThreadLocal<>();

    /**
     * 获取当前线程的数据源
     * @return
     */
    public static DataSourceType getDataSource() {
        return DATASOURCE_HOLDER.get();
    }

    /**
     * 设置数据源
     * @param dataSourceType
     */
    public static void setDataSource(DataSourceType dataSourceType) {
        DATASOURCE_HOLDER.set(dataSourceType);
    }

    /**
     * 删除当前数据源
     */
    public static void removeDataSource() {
        DATASOURCE_HOLDER.remove();
    }
}
```

### 3.3 动态数据源实现

创建一个 DynamicDataSource 类，继承自 AbstractRoutingDataSource 抽象类，重写类中的 `determineCurrentLookupKey()` 方法和 `afterPropertiesSet()` 方法：
```java
@Component
@Primary // 设置为主要注入的 Bean 数据源
public class DynamicDataSource extends AbstractRoutingDataSource {
    // 订单数据源
    @Autowired
    private DataSource orderDataSource;
    // 商品数据源
    @Autowired
    private DataSource goodsDataSource;

    // 返回当前数据源标识
    @Override
    protected Object determineCurrentLookupKey() {
        return DataSourceContextHolder.getDataSource();
    }

    @Override
    public void afterPropertiesSet() {
        // 为 targetDataSources 初始化所有数据源
        Map<Object, Object> targetDataSources = new HashMap<>();
        targetDataSources.put(DataSourceType.ORDER, orderDataSource);
        targetDataSources.put(DataSourceType.GOODS, goodsDataSource);
        super.setTargetDataSources(targetDataSources);
        // 默认数据源
        super.setDefaultTargetDataSource(orderDataSource);
        super.afterPropertiesSet();
    }
}
```
determineCurrentLookupKey 方法决定了当前线程使用的数据源标识。在 afterPropertiesSet 方法中为 targetDataSources 初始化所有数据源，并设置默认的数据源为订单数据源。

### 3.4 数据源配置类

将每一个数据源都作为一个 Bean 对象注入到 IOC 容器里面：
```java
@Configuration
public class DataSourceConfig {

    // 订单数据源
    @Bean
    @ConfigurationProperties(prefix = "spring.datasource.order")
    public DataSource orderDataSource() {
        // 底层会自动拿到 spring.datasource.order 中的配置创建一个 DruidDataSource
        return DruidDataSourceBuilder.create().build();
    }

    // 商品数据源
    @Bean
    @ConfigurationProperties(prefix = "spring.datasource.goods")
    public DataSource goodsDataSource() {
        // 底层会自动拿到 spring.datasource.order 中的配置创建一个 DruidDataSource
        return DruidDataSourceBuilder.create().build();
    }
}
```

## 4. AOP+注解实现

相比之前方案，AOP+注解实现方案可以实现更方便的动态切换。

### 4.1 自定义数据源注解

这里首先创建一个自定义注解 `@DS`，后面通过 AOP 切面拦截这个注解标记的方法，然后动态切换数据源：
```java
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
public @interface DS {
    // 默认数据源-订单数据源
    DataSourceType value() default DataSourceType.ORDER;
}
```
自定义的 `@DS` 注解，作用域为 METHOD 方法上，由于 `@DS` 中设置的默认值是 `DataSourceType.ORDER`，因此在调用订单数据源时，可以不用进行传值。

### 4.2 AOP切面实现数据源切换

创建一个 AOP 切面类，用于拦截 `@DS` 注解，实现动态数据源的切换功能：
```java
@Aspect
@Component
@Slf4j
public class DynamicDataSourceAspect {
    // 定义切点：所有被@DS注解的方法
    @Pointcut("@annotation(com.spring.example.annotation.DS)")
    public void dynamicDataSourcePointcut() {
    }

    // 在方法执行前切换数据源
    @Before("dynamicDataSourcePointcut()")
    public void before(JoinPoint point) throws Throwable {
        // 获取方法上的@DS注解
        MethodSignature signature = (MethodSignature) point.getSignature();
        Method method = signature.getMethod();
        DS dsAnnotation = method.getAnnotation(DS.class);
        if (dsAnnotation == null) {
            // 如果方法上没有，尝试获取类上的注解
            Class<?> targetClass = point.getTarget().getClass();
            dsAnnotation = targetClass.getAnnotation(DS.class);
        }
        // 切换数据源
        if (Objects.nonNull(dsAnnotation)) {
            DataSourceType dataSourceType = dsAnnotation.value();
            log.debug("切换数据源到: {}，方法: {}", dataSourceType.getName(), method.getName());
            DataSourceContextHolder.setDataSource(dataSourceType);
        }
    }

    // 在方法执行后清除数据源设置
    @After("dynamicDataSourcePointcut()")
    public void after(JoinPoint joinPoint) {
        DataSourceContextHolder.removeDataSource();
        log.debug("清除数据源设置，方法: {}", joinPoint.getSignature().getName());
    }
}
```

## 5. 实体类

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

## 6. MyBatis 配置文件

### 6.1 创建 Mapper XML 定义映射配置

在 `resources/mapper/` 目录下创建 GoodsMapper.xml 和 OrderMapper.xml 文件。

GoodsMapper.xml 文件如下所示：
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper
        PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<!-- namespace 命名空间 -->
<mapper namespace="com.spring.example.mapper.GoodsMapper">

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
<mapper namespace="com.spring.example.mapper.OrderMapper">

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

#### 6.2 定义 Mapper 数据层接口

在 `com.spring.example.mapper` 包路径下创建 GoodsMapper 和 OrderMapper 类：
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

## 7. Service层实现

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
    @DS(DataSourceType.GOODS)
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
    @DS
    public List<Order> getList() {
        List<Order> orders = orderMapper.selectAll();
        return orders;
    }
}
```

可以看到 getList 方法通过注解 `@DS` 来动态切换数据源从而实现不同方法访问不同数据库的能力，GoodsService 中的 getList 方法通过为注解提供商品数据源类型 `@DS(DataSourceType.GOODS)` 来访问商品数据库，同理 OrderService 通过注解 `@DS` (默认数据源可以不填写数据源类型)来访问订单数据库。

## 8. Controller层实现

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

## 9. 效果

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

> [完整代码实现](https://github.com/sjf0115/spring-example/tree/main/spring-boot-dynamic-datasource-aop)
