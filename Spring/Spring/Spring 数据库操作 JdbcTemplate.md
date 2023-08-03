## 1. 什么是 JdbcTemplate

大家先回顾一下我们是如何操作数据库的？一般使用 JDBC 接口直接访问关系数据库，具体如下所示：
```java
Connection conn = null;
try {
    // JDBC4 之后不需要再显式通过 Class.forName 注册驱动
    // Class.forName(DRIVER);
    // 1. 获得数据库连接
    conn = DriverManager.getConnection(URL, "root", "root");
    // 2. 创建 PreparedStatement
    PreparedStatement statement = conn.prepareStatement(sql);
    // 3. 执行查询
    ResultSet rs = statement.executeQuery();
    // 遍历查询结果
    while(rs.next()){
        int id  = rs.getInt("id");
        ...
    }
} catch (SQLException e) {
    e.printStackTrace();
} finally {
    // 4. 关闭连接
    try {
        if (!Objects.equals(conn, null)) {
            conn.close();
        }
    } catch (SQLException e) {
        e.printStackTrace();
    }
}
```
> 详细代码请查阅：[]()

通过 JDBC 接口访问数据库每次需要获取数据库连接、创建 PreparedStatement、执行SQL查询，最后关闭连接等等，操作还是比较繁琐的。Spring 中提供了一个对象，对 Jdbc 操作进行了封装，使其更简单，这就是本文要讲的 Spring JdbcTemplate。

Spring JdbcTemplate 具体是什么呢？Spring JdbcTemplate 是 Spring 框架中提供的一个对象，是对原始 JDBC API 对象的简单封装。用于和数据库交互，实现对表的 CRUD 操作。好处是 Spring 为我们提供了很多的操作模板，例如操作关系型数据的 JdbcTemplate 和 HibernateJdbcTemplate，操作 NoSQL 数据库的 RedisTemplate，操作消息队列的 JmsTemplate 等。

## 2. 快速入门

### 2.1 添加坐标依赖

在这关系型数据库我们选择的是 MySQL，所以需要引入 MySQL 的坐标依赖：
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.22</version>
</dependency>
```
在这使用 Spring JdbcTemplate 来操作关系型数据库，需要引入 Spring 的相关坐标依赖：
```xml
<!-- Spring -->
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-jdbc</artifactId>
    <version>5.2.10.RELEASE</version>
</dependency>

<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-context</artifactId>
    <version>5.2.10.RELEASE</version>
</dependency>

<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-tx</artifactId>
    <version>5.2.10.RELEASE</version>
</dependency>
```

### 2.2 创建数据库表和实体类

```sql
CREATE TABLE `tb_book` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `type` varchar(20) DEFAULT NULL,
    `name` varchar(50) DEFAULT NULL,
    `description` varchar(255) DEFAULT NULL,
    PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

```java
public class Book {
    private Integer id;
    private String type;
    private String name;
    private String description;

    public Book() {
    }

    public Book(Integer id, String type, String name, String description) {
        this.id = id;
        this.type = type;
        this.name = name;
        this.description = description;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    @Override
    public String toString() {
        return "Book{" +
                "id=" + id +
                ", type='" + type + '\'' +
                ", name='" + name + '\'' +
                ", description='" + description + '\'' +
                '}';
    }
}
```
### 2.3 使用 JdbcTemplate 访问数据库

使用 JdbcTemplate 访问数据库可以简化为三步：第一步创建数据源(使用 Spring 内置的数据源 DriverManagerDataSource)，第二步创建 JDBCTemplate，最后一步执行 SQL 即可：
```java
// 1. 创建数据源 Spring 内置的数据源
DriverManagerDataSource dataSource = new DriverManagerDataSource();
dataSource.setUrl("jdbc:mysql://localhost:3306/test?useSSL=false&characterEncoding=utf8");
dataSource.setDriverClassName("com.mysql.jdbc.Driver");
dataSource.setUsername("root");
dataSource.setPassword("root");

// 2. 创建 JDBCTemplate
JdbcTemplate template = new JdbcTemplate();
template.setDataSource(dataSource);

// 3. 执行 SQL
template.execute("INSERT INTO tb_book (type, name, description) VALUES('计算机理论', '深入理解 MyBatis', '好书')");
```

## 3. Spring 操作 JdbcTemplate

上面是我们自己手动在应用程序中创建模板对象 JdbcTemplate 和数据源 DataSource，一般来说应用程序本身不负责依赖对象的创建和维护，而是交由 Spring 来创建和维护。所以我们可以将模板对象 JdbcTemplate 和数据源 DataSource 的创建权交给 Spring，在 Spring 容器内部将数据源 DataSource 注入到 JdbcTemplate 模板对象中，具体配置如下所示：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">

    <!--  配置 JDBCTemplate  -->
    <bean id="jdbcTemplate" class="org.springframework.jdbc.core.JdbcTemplate">
        <property name="dataSource" ref="dataSource"/>
    </bean>

    <!--  配置数据源  -->
    <bean id="dataSource" class="org.springframework.jdbc.datasource.DriverManagerDataSource">
        <property name="driverClassName" value="com.mysql.jdbc.Driver"/>
        <property name="url" value="jdbc:mysql://localhost:3306/test?useSSL=false&amp;characterEncoding=utf8"/>
        <property name="username" value="root"/>
        <property name="password" value="root"/>
    </bean>
</beans>
```
配置上面之后我们实际执行一下，首先加载配置文件创建容器对象，根据容器对象获取模板对象 JDBCTemplate，最后直接执行 SQL 语句即可：
```java
// 加载配置文件得到上下文对象 即 容器对象
ApplicationContext ctx = new ClassPathXmlApplicationContext("applicationContext-xml.xml");
// 获取 JDBCTemplate 数据源是通过 XML 注入
JdbcTemplate template = (JdbcTemplate) ctx.getBean("jdbcTemplate");

// 执行 SQL
template.execute("INSERT INTO tb_book (type, name, description) VALUES('计算机理论', '深入理解 MyBatis', '好书')");
```

## 4. JdbcTemplate 常见操作

JdbcTemplate 中以 update 开头的方法，用来执行增、删、改操作：

![](../../Image/Spring/spring-jdbctemplate-1.png)

以 query 开头的方法，用来执行查询操作：

![](../../Image/Spring/spring-jdbctemplate-2.png)

| 方法 | 说明 |
| :------------- | :------------- |
| execute | 单语句执行，一般用来执行 DDL 语句 |
| query | 将查询结果集封装为 JavaBean 对象 |
| queryForObject | 将查询结果集封装为对象 |
| queryForList | 将查询结果集封装为 List 集合 |
| queryForMap | 将查询结果集封装为 Map 集合 |
| queryForRowSet | 将查询结果集封装为 SqlRowSet |
| update | 执行单语句的更新操作，一般用来执行插入、更新或删除语句 |
| batchUpdate | 批量执行多个更新操作 |


### 4.1 DDL

可以使用 execute 方法来执行 DDL 操作，例如如下所示的创建表和删除表操作：
```java
// 加载配置文件得到上下文对象 即 容器对象
ApplicationContext ctx = new ClassPathXmlApplicationContext("applicationContext-xml.xml");
// 获取 JDBCTemplate 数据源是通过 XML 注入
JdbcTemplate template = (JdbcTemplate) ctx.getBean("jdbcTemplate");

// DDL - 创建表
template.execute("CREATE TABLE `tb_book_2` (\n" +
        "    `id` int(11) NOT NULL AUTO_INCREMENT,\n" +
        "    `type` varchar(20) DEFAULT NULL,\n" +
        "    `name` varchar(50) DEFAULT NULL,\n" +
        "    `description` varchar(255) DEFAULT NULL,\n" +
        "    PRIMARY KEY (`id`) USING BTREE\n" +
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8;");

// DDL - 删除表
template.execute("DROP TABLE `tb_book_2`;");
```

### 4.2 DML-插入

JdbcTemplate 中以 update 开头的方法，用来执行增、删、改操作。update 方法只能执行单语句，如果想批量执行增加、删除、修改操作可以使用 batchUpdate。先看一个最简单的情况，没有参数直接在 SQL 中写死：
```java
String sql = "INSERT INTO tb_book (type, name, description) VALUES('计算机理论', '深入理解 JdbcTemplate', '1')";
int nums = template.update(sql);
System.out.println("成功插入" + nums + "条记录");
```
一般最常用的还是在 SQL 中动态指定变量，这个使用可以使用 `?` 占位符：
```java
String sql = "INSERT INTO tb_book (type, name, description) VALUES(?, ?, ?)";
String type = "计算机理论";
String name = "深入理解 JdbcTemplate";
String desc = "2";
int nums2 = template.update(sql, type, name, desc);
System.out.println("成功插入" + nums2 + "条记录");
```
此外也还可以通过 PreparedStatementSetter 来设置参数，它是个函数式接口，内部有个 setValues 方法会传递一个 PreparedStatement参数：
```java
String sql = "INSERT INTO tb_book (type, name, description) VALUES(?, ?, ?)";
String type = "计算机理论";
String name = "深入理解 JdbcTemplate";
String desc = "3";
int nums3 = template.update(sql, new PreparedStatementSetter() {
    @Override
    public void setValues(PreparedStatement ps) throws SQLException {
        ps.setString(1, type);
        ps.setString(2, name);
        ps.setString(3, desc);
    }
});
System.out.println("成功插入" + nums3 + "条记录");
```
有时候我们可能还需要返回插入行的自增ID，这个时候可以使用如下语句来获取：
```java
String sql = "INSERT INTO tb_book (type, name, description) VALUES(?, ?, ?)";
String type = "计算机理论";
String name = "深入理解 JdbcTemplate";
String desc = "4";
KeyHolder keyHolder = new GeneratedKeyHolder();
int nums4 = template.update(new PreparedStatementCreator() {
    @Override
    public PreparedStatement createPreparedStatement(Connection con) throws SQLException {
        //手动创建PreparedStatement，注意第二个参数：Statement.RETURN_GENERATED_KEYS
        PreparedStatement ps = con.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
        ps.setString(1, type);
        ps.setString(2, name);
        ps.setString(3, desc);
        return ps;
    }
}, keyHolder);
System.out.println("成功插入" + nums4 + "条记录");
System.out.println("新记录id：" + keyHolder.getKey().intValue());
```
上面几个示例一次只能操作一条记录，如果想批量插入多条记录怎么办呢？可以使用 batchUpdate 方法来批量操作，具体如下所示：
```java
String sql = "INSERT INTO tb_book (type, name, description) VALUES(?, ?, ?)";
List<Object[]> books = Arrays.asList(
        new Object[]{"计算机理论", "深入理解 JdbcTemplate", "51"},
        new Object[]{"计算机理论", "深入理解 JdbcTemplate", "52"},
        new Object[]{"计算机理论", "深入理解 JdbcTemplate", "53"},
        new Object[]{"计算机理论", "深入理解 JdbcTemplate", "54"});
int[] numsBatch = template.batchUpdate(sql, books);
for (int num : numsBatch) {
    System.out.println("批量插入" + num + "条记录");
}
```

### 4.2 DML-删除

JdbcTemplate 中删除操作与插入操作一样，都是以 update 开头的方法来执行单语句操作，使用 batchUpdate 执行批量操作。下面具体演示一个删除操作，详细可以参考插入操作：
```java
// 加载配置文件得到上下文对象 即 容器对象
ApplicationContext ctx = new ClassPathXmlApplicationContext("applicationContext-xml.xml");
// 获取 JDBCTemplate 数据源是通过 XML 注入
JdbcTemplate template = (JdbcTemplate) ctx.getBean("jdbcTemplate");

// 执行 SQL
int startId = 15;
int endId = 24;
int nums = template.update("DELETE FROM tb_book WHERE id >= ? AND id <= ?", startId, endId);
System.out.println("成功删除" + nums + "条记录");
```

### 4.3 DML-修改

JdbcTemplate 中修改操作与插入操作一样，都是以 update 开头的方法来执行单语句操作，使用 batchUpdate 执行批量操作。下面具体演示一个更新操作，详细可以参考插入操作：
```java
// 加载配置文件得到上下文对象 即 容器对象
ApplicationContext ctx = new ClassPathXmlApplicationContext("applicationContext-xml.xml");
// 获取 JDBCTemplate 数据源是通过 XML 注入
JdbcTemplate template = (JdbcTemplate) ctx.getBean("jdbcTemplate");

// 执行 SQL
String name = "深入理解 JdbcTemplate";
int id = 26;
int nums = template.update("Update tb_book SET name = ? WHERE id = ?", name, id);
System.out.println("成功更新" + nums + "条记录");
```

### 4.4 DML-查询




...
