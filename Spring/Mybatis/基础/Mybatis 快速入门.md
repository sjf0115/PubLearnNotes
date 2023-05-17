实现一个简单的 MyBatis 快速入门项目，可以根据如下几步来快速完成：
- 数据准备：创建 `tb_user` 表，添加数据
- 创建模块，导致坐标
- 编写 Mybatis 核心配置文件 `mybatis-config.xml`：替换连接信息，解决硬编码问题
- 编写 SQL 映射文件 `UserMapper.xml`：统一管理 SQL 语句
- 编码
  - 定义 POJO 类 `User`
  - 加载核心配置文件，获取 `SqlSessionFactory` 对象
  - 获取 `SqlSession` 对象，执行 SQL 语句
  - 释放资源

## 1. 准备数据

在这我们在 test 数据库中创建 tb_user 数据表并添加 5 条记录用来测试：
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

INSERT INTO tb_user VALUES (1, 'Jone', 18, 'jone@163.com');
INSERT INTO tb_user VALUES (2, 'Jack', 20, 'jack@163.com');
INSERT INTO tb_user VALUES (3, 'Tom', 28, 'tom@163.com');
INSERT INTO tb_user VALUES (4, 'Sandy', 21, 'sandy@163.com');
INSERT INTO tb_user VALUES (5, 'Billie', 24, 'billie@163.com');
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

Mybatis XML 配置文件中包含了对 MyBatis 系统的核心设置，包括获取数据库连接实例的数据源（DataSource）以及决定事务作用域和控制方式的事务管理器（TransactionManager）。后面会再探讨 XML 配置文件的详细内容，这里先给出一个简单的示例，如下是快速部署项目的 `mybatis-config.xml` 配置文件：
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
        <!-- 映射器配置 下一步会具体介绍 -->
        <mapper resource="UserMapper.xml"/>
    </mappers>
</configuration>
```
当然，还有很多可以在 XML 文件中配置的选项，上面的示例仅罗列了最关键的部分。注意 XML 头部的声明，它用来验证 XML 文档的正确性。environment 元素体中包含了事务管理和连接池的配置。mappers 元素则包含了一组映射器（mapper），这些映射器的 XML 映射文件包含了 SQL 代码和映射定义信息。

## 4. SQL Mapper 映射文件

SQL Mapper 映射文件中定义了 SQL 查询语句实现与数据库的交互，主要目的是实现 SQL 的统一管理。一个 SQL 语句既可以通过 XML 定义，也可以通过注解定义。因为 MyBatis 提供的所有特性都可以利用基于 XML 的映射语言来实现，所以在这我们先看看 XML 如何定义语句的。 如下所示，在模块的 resources 目录下创建映射配置文件 `UserMapper.xml`：
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper
        PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<!-- namespace 命名空间 -->
<mapper namespace="com.mybatis.example.mapper.UserMapper">
    <!-- 查询所有的用户  id 唯一标识 resultType 返回类型-->
    <select id="selectAll" resultType="com.mybatis.example.pojo.User">
        select * from tb_user;
    </select>

    <select id="selectById" resultType="com.mybatis.example.pojo.User">
        select * from tb_user where id = #{id};
    </select>
</mapper>
```
我们在命名空间 `com.mybatis.example.mapper.UserMapper` 中定分别定义了名为 `selectAll` 和 `selectById` 的映射语句。这样你就可以用全限定名 `com.mybatis.example.mapper.UserMapper.selectAll` 和 `com.mybatis.example.mapper.UserMapper.selectById` 来调用映射语句分别完成所有用户的查询和根据指定的 Id 的用户查询，如下所示(后面会详细介绍)：
```java
User user = session.selectOne("com.mybatis.example.mapper.UserMapper.selectById", 1);
```

> 命名空间的作用有两个，一个是利用更长的全限定名来将不同的语句隔离开来，同时也实现我们下面要说的 Mapper 接口绑定(下面详细介绍)。就算你觉得暂时用不到接口绑定，你也应该遵循这里的规定，以防哪天你改变了主意。 长远来看，只要将命名空间置于合适的 Java 包命名空间之中，你的代码会变得更加整洁，也有利于你更方便地使用 MyBatis。

配置完 配置文件之后，别忘记在 `mybatis-config.xml` 配置中添加 mapper：
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

从 SQL 映射文件 `UserMapper.xml` 可以看到两个查询语句的返回类型都是 POJO 类 `User`，所以在这创建对应的 POJO 类：
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

从 XML 文件中构建 SqlSessionFactory 的实例非常简单，建议使用类路径下的资源文件进行配置。但也可以使用任意的输入流（InputStream）实例，比如用文件路径字符串或 `file:// URL` 构造的输入流。MyBatis 包含一个名叫 Resources 的工具类，它包含一些实用方法，使得从类路径或其它位置加载资源文件更加容易：
```java
String resource = "mybatis-config.xml";
InputStream inputStream = Resources.getResourceAsStream(resource);
SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder().build(inputStream);
```
因为 `mybatis-config.xml` 配置文件是在 resource 根目录下，所以可以直接使用文件名来加载 Mybatis 的核心配置文件。

### 5.3 获取 SqlSession 执行 SQL

既然有了 SqlSessionFactory，顾名思义，我们可以从中获得 SqlSession 的实例。SqlSession 提供了在数据库执行 SQL 命令所需的所有方法。有两种方式来执行 SQL 命令，具体如下所示。

#### 5.3.1 指定 SQL 语句唯一标识

你可以通过 SqlSession 实例的 `selectList` 和 `selectOne` 方法来分别执行查询所有用户以及根据指定用户ID查询用户的 SQL 语句，在这你需要指定 SQL 语句在 UserMapper.xml 文件中定义的 SQL 唯一标识(或者全限定名)，具体如下所示：
```java
// 获取 SqlSession 对象
SqlSession session = sqlSessionFactory.openSession();

// 查询所有的用户
    // 参数是 SQL 语句的唯一标识 Mapper.xml 文件中定义
List<User> users = session.selectList("com.mybatis.example.mapper.UserMapper.selectAll");
for (User user : users) {
    System.out.println("全部用户: " + user);
}

// 根据指定的ID查询用户
User user = session.selectOne("com.mybatis.example.mapper.UserMapper.selectById", 1);
System.out.println("目标用户: " + user);
```

> 我们在命名空间 `com.mybatis.example.mapper.UserMapper` 中定分别定义了唯一标识为 `selectAll` 和 `selectById` 的 SQL 映射语句。这样你就可以用全限定名 `com.mybatis.example.mapper.UserMapper.selectAll` 和 `com.mybatis.example.mapper.UserMapper.selectById` 来调用映射语句分别完成所有用户的查询和根据指定的 Id 的用户查询。

> 完整代码请查阅：[MybatisQuickStart](https://github.com/sjf0115/spring-example/blob/main/mybatis-quick-start/src/main/java/com/mybatis/example/MybatisQuickStart.java)

#### 5.3.2 Mapper 代理开发

你可能会注意到，上面这种方式和用全限定名调用 Java 对象的方法类似。将上面的命名直接映射到在命名空间中同名的映射器 Mapper 类，并将已映射的 SELECT 语句匹配到对应名称、参数和返回类型的方法：
```java
public interface UserMapper {
    List<User> selectAll();
    User selectById(@Param("id") int id);
}
```

因此你就可以像上面那样，不费吹灰之力地在对应的映射器接口调用方法，如下所示：
```java
// 查询所有的用户
UserMapper mapper = session.getMapper(UserMapper.class);
List<User> users = mapper.selectAll();
for (User user : users) {
    System.out.println("全部用户: " + user);
}

// 根据指定的ID查询用户
User user = mapper.selectById(1);
System.out.println("目标用户: " + user);
```
这种方法有很多优势，首先它不依赖于字符串字面值，会更安全一点；其次，如果你的 IDE 有代码补全功能，那么代码补全可以帮你快速选择到映射好的 SQL 语句。


我们总结一下使用 Mapper 代理开发必须满足的要求：
- 定义与 SQL 映射文件同名的 Mapper 接口
- 设置 SQL 映射文件的 namespace 属性为 Mapper 接口全限定名

![](../../../Image/Mybatis/mybatis-quick-start-1.png)

- 在 Mapper 接口中定义的方法名与 SQL 映射文件中 SQL 语句的 id 保持一致，参数类型和返回值类型也要保持一致

> 完整代码请查阅：[MybatisQuickStartMapper](https://github.com/sjf0115/spring-example/blob/main/mybatis-quick-start/src/main/java/com/mybatis/example/MybatisQuickStartMapper.java)
