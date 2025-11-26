作为企业级应用开发的核心组成部分，数据访问层的性能与稳定性直接关系到整个系统的质量。今天我将为大家详细介绍如何在 Spring Boot 项目中集成 MyBatis 和 Druid，打造高效可靠的数据访问解决方案。

## 1. 技术栈简介

### 1.1 Spring Boot

Spring Boot 通过自动配置和起步依赖极大简化了 Spring 应用的初始搭建和开发过程。

### 1.2 MyBatis

MyBatis 是一款优秀的持久层框架，它支持定制化 SQL、存储过程以及高级映射，避免了几乎所有的 JDBC 代码和手动设置参数。

### 1.3 Druid

Druid 是阿里巴巴开源的高性能数据库连接池，提供了强大的监控和扩展功能。

## 2. 项目搭建与配置

### 2.1 创建 Spring Boot 项目

首先使用 Spring Initializr 创建项目，选择以下依赖：
- Spring Web
- MyBatis Framework
- MySQL Driver

### 2.2 添加依赖

在 `pom.xml` 中添加必要依赖：
```xml
<dependencies>
    <!-- Spring Boot Starter -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- MyBatis Spring Boot Starter -->
    <dependency>
        <groupId>org.mybatis.spring.boot</groupId>
        <artifactId>mybatis-spring-boot-starter</artifactId>
        <version>${mybatis.spring.version}</version>
    </dependency>

    <!-- MySQL 驱动 -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
    </dependency>

    <!-- Druid 连接池 -->
    <dependency>
        <groupId>com.alibaba</groupId>
        <artifactId>druid-spring-boot-starter</artifactId>
        <version>${druid.spring.version}</version>
    </dependency>

    <!-- Lombok 简化代码 -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
    </dependency>
</dependencies>
```

### 2.3 配置文件

在 `application.yml` 中配置数据源和 MyBatis：

```
# 指定数据源类型为 Druid 第一种通用配置方式：通过 type:com.alibaba.druid.pool.DruidDataSource 配置
spring:
  datasource:
    type: com.alibaba.druid.pool.DruidDataSource
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/test?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true
    username: root
    password: root

mybatis:
  # 指定 mapper.xml 文件路径
  mapper-locations: classpath:mapper/*.xml
  # 指定实体类包路径 xxxMapper.xml 不用指定全限定名
  type-aliases-package: com.spring.example.bean
  configuration:
    # 开启驼峰命名转换
    map-underscore-to-camel-case: true
```
更推荐指定数据源类型为 Druid 第二种专用配置方式：
```
# 指定数据源类型为 Druid 第二种专用配置方式：通过 druid: 配置
spring:
  datasource:
    druid:
      driver-class-name: com.mysql.cj.jdbc.Driver
      url: jdbc:mysql://localhost:3306/test?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true
      username: root
      password: root

...
```

## 3. 实体类

在 `com.spring.example.bean` 包路径下定义 POJO 实体类 User：
```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User {
    private Long id;
    private String name;
    private int age;
}
```

## 4. MyBatis 配置文件

### 4.1 创建 Mapper XML 定义映射配置

在 `resources/mapper/` 目录下创建 UserMapper.xml 文件：
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper
        PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<!-- namespace 命名空间 -->
<mapper namespace="com.spring.example.mapper.UserMapper">

    <!-- type="User" 需要与配置文件 type-aliases-package 参数配合-->
    <resultMap id="BaseResultMap" type="com.spring.example.bean.User">
        <id column="id" jdbcType="BIGINT" property="id" />
        <result column="name" jdbcType="VARCHAR" property="name" />
        <result column="age" jdbcType="INTEGER" property="age" />
    </resultMap>

    <sql id="Base_Column_List">
        id, name, age
    </sql>

    <!-- 查询所有的用户 -->
    <select id="selectAll" resultMap="BaseResultMap">
        SELECT
        <include refid="Base_Column_List" />
        FROM tb_user
    </select>

    <!-- 根据指定的 Id 查询用户 -->
    <select id="selectById" parameterType="java.lang.Long" resultMap="BaseResultMap">
        SELECT
        <include refid="Base_Column_List" />
        FROM tb_user
        WHERE id = #{id}
    </select>
</mapper>
```
Mapper 映射文件中定义了 SQL 查询语句实现与数据库的交互，主要目的是实现 SQL 的统一管理。一个 SQL 语句既可以通过 XML 定义，也可以通过注解定义。因为 MyBatis 提供的所有特性都可以利用基于 XML 的映射语言来实现，在这我们采用 XML 来定义语句。

#### 4.2 定义 Mapper 数据层接口

```java
@Mapper
public interface UserMapper {
    List<User> selectAll();
    User selectById(Long id);
}
```

## 5. Service

Service 层 UserService 中提供 getList 和 getDetail 方法来获取所有用户和指定ID的用户：
```java
@Service
public class UserService {
    @Resource
    private UserMapper userMapper;

    /**
     * 获取用户列表
     * @return
     */
    public List<User> getList() {
        List<User> users = userMapper.selectAll();
        return users;
    }

    /**
     * 根据用户ID获取用户详细信息
     * @param id
     * @return
     */
    public Optional<User> getDetail(Long id) {
        User user = userMapper.selectById(id);
        if (user == null) {
            return Optional.empty();
        }
        return Optional.of(user);
    }
}
```

## 6. Controller

Controller 层 UserController 中提供 getList 和 getDetail 接口获取所有用户和指定ID的用户：
```java
@Slf4j
@RestController
@RequestMapping(value = "/user", produces = MediaType.APPLICATION_JSON_VALUE)
public class UserController {
    @Autowired
    private UserService userService;

    @GetMapping(value = "/list")
    public List<User> getList() {
        List<User> users = userService.getList();
        return users;
    }

    @GetMapping(value = "/detail")
    public User getDetail(@RequestParam Long id) {
        Optional<User> userOptional = userService.getDetail(id);
        return userOptional.orElse(null);
    }
}
```

## 7. 效果

请求 `http://localhost:8090/user/list` 接口获取所有用户：
```json
[
  {
    "id": 1,
    "name": "Jone",
    "age": 18
  },
  {
    "id": 2,
    "name": "Jack",
    "age": 20
  },
  {
    "id": 3,
    "name": "Tom",
    "age": 28
  },
  {
    "id": 4,
    "name": "Sandy",
    "age": 21
  },
  {
    "id": 5,
    "name": "Billie",
    "age": 24
  }
]
```
请求 `http://localhost:8090/user/detail?id=1` 接口获取 id 等于 1 的用户：
```json
{
  "id": 1,
  "name": "Jone",
  "age": 18
}
```

> [完整代码实现](https://github.com/sjf0115/spring-example/tree/main/spring-boot-mybatis-druid)
