在 Spring Boot 应用中，JdbcTemplate 是 Spring 框架提供的一个强大且易于使用的数据库访问工具。它简化了传统的 JDBC 操作，减少了大量的样板代码，同时保持了灵活性和控制力。本文将详细介绍如何使用 JdbcTemplate 在 Spring Boot 应用中实现 MySQL 数据库的增删改查功能。

## 1. 创建工程

首先通过 Spring Initializr 来快速搭建一个 SpringBoot 项目，部分 pom 依无需手动添加赖，也无需自己编写引导类，相对更方便一些。通过 Spring Initializr 快速搭建点击 Spring Initializr 选项而不是 Maven 选项：

![](img-spring-boot-mybatis-1.png)

这里我们创建的是 Web工程，所以选中 web 即可：

![](img-spring-boot-mybatis-2.png)

此外还需要选中 MySQL。

工程创建之后会自动生成的引导类如下所示：
```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class SpringBootJdbcTemplateApplication {
    public static void main(String[] args) {
        SpringApplication.run(SpringBootJdbcTemplateApplication.class, args);
    }
}
```
最终依赖如下所示：
```xml
<!-- Web开发需要的起步依赖 -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>

<!-- 集成 JDBC -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jdbc</artifactId>
</dependency>

<!-- MySQL -->
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
</dependency>

<!-- 其他依赖 -->

<!-- Lombok -->
<dependency>
    <groupId>org.projectlombok</groupId>
    <artifactId>lombok</artifactId>
</dependency>
```

## 2. 配置数据源参数

在 `application.yml` 中配置数据源参数如下所示：
```
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/test?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true
    username: root
    password: root
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

## 4. 数据访问层

在数据访问层 UserDao 中提供一些列方法来实现用户的增删改查能力：
```java
@Repository
public class UserDao {
    @Autowired
    JdbcTemplate jdbcTemplate;

    // 插入用户
    public int save(User user) {
        String sql = "INSERT INTO tb_user (id, name, age) VALUES (?, ?, ?)";
        return jdbcTemplate.update(sql, user.getId(), user.getName(), user.getAge());
    }

    // 更新用户
    public int update(User user) {
        String sql = "UPDATE tb_user SET name = ?, age = ? WHERE id = ?";
        return jdbcTemplate.update(sql, user.getName(), user.getAge(), user.getId());
    }

    // 根据 ID 删除用户
    public int deleteById(Long id) {
        String sql = "DELETE FROM tb_user WHERE id = ?";
        return jdbcTemplate.update(sql, id);
    }

    // 根据 ID 查询用户
    public User selectById(Long id) {
        String sql = "SELECT * FROM tb_user WHERE id = ?";

        try {
            return jdbcTemplate.queryForObject(sql, new UserRowMapper(), id);
        } catch (EmptyResultDataAccessException e) {
            return null; // 没有找到记录时返回 null
        }
    }

    // 查询所有用户
    public List<User> selectAll() {
        String sql = "SELECT * FROM tb_user";
        return jdbcTemplate.query(sql, new UserRowMapper());
    }

    // 自定义 RowMapper
    private static class UserRowMapper implements RowMapper<User> {
        @Override
        public User mapRow(ResultSet rs, int rowNum) throws SQLException {
            User user = new User();
            user.setId(rs.getLong("id"));
            user.setName(rs.getString("name"));
            user.setAge(rs.getInt("age"));
            return user;
        }
    }
}
```


## 5. Service

Service 层 UserService 中提供对应的一些列方法来实现用户服务能力：
```java
@Service
public class UserService {
    @Autowired
    private UserDao userDao;

    // 插入用户
    public int save(User user) {
        return userDao.save(user);
    }

    // 更新用户
    public int update(User user) {
        return userDao.update(user);
    }

    // 根据 ID 删除用户
    public int deleteById(Long id) {
        return userDao.deleteById(id);
    }

    // 获取用户列表
    public List<User> getList() {
        return userDao.selectAll();
    }

    // 根据 ID 查询用户
    public User getDetail(Long id) {
        return userDao.selectById(id);
    }
}
```

## 6. 控制器层

控制器层 UserController 中提供用户接口来操作用户：
```java
@Slf4j
@RestController
@RequestMapping(value = "/user", produces = MediaType.APPLICATION_JSON_VALUE)
public class UserController {
    @Autowired
    private UserService userService;

    @GetMapping(value = "/list")
    public List<User> getList() {
        return userService.getList();
    }

    @GetMapping(value = "/detail")
    public User getDetail(@RequestParam Long id) {
        return userService.getDetail(id);
    }

    @DeleteMapping(value = "/delete")
    public int delete(@RequestParam Long id) {
        return userService.deleteById(id);
    }

    @PostMapping(value = "/update")
    public int update(@RequestBody User user) {
        return userService.update(user);
    }

    @PostMapping(value = "/save")
    public int save(@RequestBody User user) {
        return userService.save(user);
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

> [完整代码实现](https://github.com/sjf0115/spring-example/tree/main/spring-boot-jdbctemplate)
