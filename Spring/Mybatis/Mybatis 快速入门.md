## 1. 查询 User 表汇总所有的数据

- 创建 User 表，添加数据
- 创建模块，导致坐标
- 编写 Mybatis 核心配置文件：替换连接信息，解决硬编码问题
- 编写 SQL 映射文件：统一管理 SQL 语句，解决硬编码问题
- 编码
  - 定义 POJO 类
  - 加载核心配置文件，获取 SqlSessionFactory 对象
  - 获取 SqlSession 对象，执行 SQL 语句
  - 释放资源

## 1. 创建 MySQL 数据表

```sql
CREATE DATABASE IF NOT EXISTS test;
USE test;

CREATE TABLE IF NOT EXISTS `tb_user` (
  `id` bigint(20) NOT NULL COMMENT '主键ID',
  `name` varchar(30) DEFAULT NULL COMMENT '姓名',
  `age` int(11) DEFAULT NULL COMMENT '年龄',
  `email` varchar(50) DEFAULT NULL COMMENT '邮箱',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
```



## 2. 配置依赖

如果使用 Maven 来构建项目，则需将下面的依赖代码置于 pom.xml 文件中：
```xml
<!-- Mybatis 核心依赖 -->
<dependency>
    <groupId>org.mybatis</groupId>
    <artifactId>mybatis</artifactId>
    <version>3.5.11</version>
</dependency>

<!-- MySQL -->
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>5.1.46</version>
</dependency>

<!-- Junit  -->
<dependency>
    <groupId>junit</groupId>
    <artifactId>junit</artifactId>
    <version>4.12</version>
    <scope>test</scope>
</dependency>

<!-- 日志 -->
<dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>slf4j-api</artifactId>
    <version>1.7.20</version>
</dependency>

<dependency>
    <groupId>ch.qos.logback</groupId>
    <artifactId>logback-classic</artifactId>
    <version>1.2.3</version>
</dependency>

<dependency>
    <groupId>ch.qos.logback</groupId>
    <artifactId>logback-core</artifactId>
    <version>1.2.3</version>
</dependency>
```

## 3. 配置 Mybatis XML 配置文件

Mybatis XML 配置文件中包含了对 MyBatis 系统的核心设置，包括获取数据库连接实例的数据源（DataSource）以及决定事务作用域和控制方式的事务管理器（TransactionManager）。后面会再探讨 XML 配置文件的详细内容，这里先给出一个简单的示例，如下是 mybatis-config.xml 配置文件：
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE configuration
        PUBLIC "-//mybatis.org//DTD Config 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-config.dtd">
<configuration>
    <!-- environments：配置数据库连接环境信息 可以配置多个 environment，通过 default 属性切换不同的 environment -->
    <environments default="prod">
        <environment id="prod">
            <transactionManager type="JDBC"/>
            <dataSource type="POOLED">
                <!--数据库连接信息-->
                <property name="driver" value="com.mysql.jdbc.Driver"/>
                <property name="url" value="jdbc:mysql:///test?useSSL=false"/>
                <property name="username" value="root"/>
                <property name="password" value="root"/>
            </dataSource>
        </environment>

        <environment id="dev">
            <transactionManager type="JDBC"/>
            <dataSource type="POOLED">
                <!--数据库连接信息-->
                <property name="driver" value="com.mysql.jdbc.Driver"/>
                <property name="url" value="jdbc:mysql:///test?useSSL=false"/>
                <property name="username" value="root"/>
                <property name="password" value="root"/>
            </dataSource>
        </environment>
    </environments>

    <mappers>
        <!-- 下一步会具体介绍 -->
        <mapper resource="UserMapper.xml"/>
    </mappers>
</configuration>
```
当然，还有很多可以在 XML 文件中配置的选项，上面的示例仅罗列了最关键的部分。注意 XML 头部的声明，它用来验证 XML 文档的正确性。environment 元素体中包含了事务管理和连接池的配置。mappers 元素则包含了一组映射器（mapper），这些映射器的 XML 映射文件包含了 SQL 代码和映射定义信息。

## 4. SQL Mapper 映射文件

一个语句既可以通过 XML 定义，也可以通过注解定义。我们先看看 XML 定义语句的方式，事实上 MyBatis 提供的所有特性都可以利用基于 XML 的映射语言来实现，这使得 MyBatis 在过去的数年间得以流行。
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper
        PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<!-- namespace 命名空间 -->
<mapper namespace="com.mybatis.example.UserMapper">
    <!-- 查询所有的用户 -->
    <select id="selectAll" resultType="com.mybatis.example.pojo.User">
        select * from tb_user;
    </select>

    <select id="selectById" resultType="com.mybatis.example.pojo.User">
        select * from tb_user where id = #{id};
    </select>
</mapper>
```
通过上面的代码，我们完成了两个查询语句的配置，一个是查询所有的用户，一个是根据指定的 Id 查询用户。


配置完 配置文件之后，别忘记在 mybatis-config.xml 配置中添加 mapper
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE configuration
        PUBLIC "-//mybatis.org//DTD Config 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-config.dtd">
<configuration>
    ...
    <mappers>
         <mapper resource="UserMapper.xml"/>
    </mappers>
</configuration>
```

## 5. 编写代码

### 5.1 定义 POJO 类

创建对应的实体类：
```java
public class User {
    // 主键ID
    private long id;
    // '姓名'
    private String name;
    // 年龄
    private int age;
    // '邮箱'
    private String email;

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    @Override
    public String toString() {
        return "User{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", age=" + age +
                ", email='" + email + '\'' +
                '}';
    }
}
```

### 5.2 从 XML 中构建 SqlSessionFactory

每个基于 MyBatis 的应用都是以一个 SqlSessionFactory 的实例为核心的。SqlSessionFactory 的实例可以通过 SqlSessionFactoryBuilder 获得。而 SqlSessionFactoryBuilder 则可以从 XML 配置文件或一个预先配置的 Configuration 实例来构建出 SqlSessionFactory 实例。

从 XML 文件中构建 SqlSessionFactory 的实例非常简单，建议使用类路径下的资源文件进行配置。 但也可以使用任意的输入流（InputStream）实例，比如用文件路径字符串或 file:// URL 构造的输入流。MyBatis 包含一个名叫 Resources 的工具类，它包含一些实用方法，使得从类路径或其它位置加载资源文件更加容易。

```java
String resource = "mybatis-config.xml";
InputStream inputStream = Resources.getResourceAsStream(resource);
SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder().build(inputStream);
```
首先是加载 Mybatis 的核心配置文件 `mybatis-config.xml`，因为该配置文件是在 resource 根目录下，所以可以直接使用 `mybatis-config.xml` 文件名即可。


### 5.3 获取 SqlSession 执行 SQL

既然有了 SqlSessionFactory，顾名思义，我们可以从中获得 SqlSession 的实例。SqlSession 提供了在数据库执行 SQL 命令所需的所有方法。

#### 5.3.1 指定 SQL 语句唯一标识

你可以通过 SqlSession 实例的 `selectList` 和 `selectOne` 方法来分别执行查询所有用户以及根据指定用户ID查询用户的 SQL 语句，在这你需要指定 SQL 语句在 UserMapper.xml 文件中定义的 SQL 唯一标识，具体如下所示：
```java
// 获取 SqlSession 对象
SqlSession session = sqlSessionFactory.openSession();

// 查询所有的用户
    // 参数是 SQL 语句的唯一标识 Mapper.xml 文件中定义
List<User> users = session.selectList("com.mybatis.example.UserMapper.selectAll");
for (User user : users) {
    System.out.println("全部用户: " + user);
}

// 根据指定的ID查询用户
User user = session.selectOne("com.mybatis.example.UserMapper.selectById", 1);
System.out.println("目标用户: " + user);
```

#### 5.3.2 指定接口

诚然，这种方式能够正常工作，对使用旧版本 MyBatis 的用户来说也比较熟悉。但现在有了一种更简洁的方式，即使用和指定语句的参数和返回值相匹配的接口，在这为 UserMapper：
```java
public interface UserMapper {
    List<User> selectAll();
    User selectById(@Param("id") int id);
}
```
现在你的代码不仅更清晰，更加类型安全，还不用担心可能出错的字符串字面值以及强制类型转换：
```java
// 查询所有的用户
UserMapper mapper = session.getMapper(UserMapper.class);
List<User> users2 = mapper.selectAll();
for (User user2 : users2) {
    System.out.println("全部用户: " + user2);
}

// 根据指定的ID查询用户
User user2 = mapper.selectById(1);
System.out.println("目标用户: " + user2);
```




...
