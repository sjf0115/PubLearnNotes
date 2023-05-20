## 1. MyBatis 是什么

MyBatis 的前身是 iBATIS，iBATIS 于 2002 年由 Clinton Begin 创建。2010 年这个项目由 Apache Software Foundation 迁移到了 Google Code，并且改名为 MyBatis。2013 年 11 月迁移到 Github。MyBatis 3 是 iBATIS 的全新设计，支持注解和 Mapper。

MyBatis 是一个简化和实现了 Java 数据持久化层的开源框架，抽象了大量的 JDBC 冗余代码，并提供了一个简单易用的 API 和数据库交互。MyBatis 消除了几乎所有的 JDBC 代码和参数的手工设置以及结果集的检索。MyBatis 流行的主要原因在于它的简单性和易使用性。在 Java 应用程序中，数据持久化层涉及到的工作有：将从数据库查询到的数据生成所需要的 Java 对象；将 Java 对象中的数据通过 SQL 持久化到数据库中。MyBatis 通过抽象底层的 JDBC 代码，自动化 SQL 结果集产生 Java 对象、Java 对象的数据持久化数据库中的过程使得对 SQL 的使用变得容易。

## 2. 为什么选择 MyBatis？

当前有很多基于 Java 的持久化框架，而 MyBatis 流行起来有以下几个原因： 
- 消除了大量的 JDBC 冗余代码
- 很低的学习成本，容易上手
- 能很好地与传统数据库协同工作
- 支持 SQL 语句查询
- 提供了与 Spring 和 Guice 框架的集成支持
- 提供了与第三方缓存类库的集成支持
- 有更好的性能

### 2.1 消除大量的 JDBC 冗余代码

Java 通过 JDBC API 来操作关系型数据库，但是 JDBC 是一个非常底层的 API，我们需要编写大量的代码来完成对数据库的操作。下面我们使用 JDBC API 来操作数据库，对表 tb_student 实现简单的 SELECT 和 INSERT 操作。假设 tb_studnet 表有 `id`、`stu_id`、`stu_name`、`status` 字段，具体如下所示：
```sql
DROP TABLE IF EXISTS `student`;
CREATE TABLE tb_student (
    -- id 主键
    id INT PRIMARY KEY AUTO_INCREMENT,
    stu_id INT NOT NULL COMMENT '学生编号',
    stu_name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    status INT NOT NULL COMMENT '状态：0:删除, 1:未删除'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```
对应的 Studnet JavaBean 定义如下：
```java
public class Student {
    // 自增ID
    private Integer id;
    // 编码
    private Integer stuId;
    // 姓名
    private String stuName;
    // 状态
    private Integer status;

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public Integer getStuId() {
        return stuId;
    }

    public void setStuId(Integer stuId) {
        this.stuId = stuId;
    }

    public String getStuName() {
        return stuName;
    }

    public void setStuName(String stuName) {
        this.stuName = stuName;
    }

    public Integer getStatus() {
        return status;
    }

    public void setStatus(Integer status) {
        this.status = status;
    }

    @Override
    public String toString() {
        return "Student{" +
                "id=" + id +
                ", stuId=" + stuId +
                ", stuName='" + stuName + '\'' +
                ", status=" + status +
                '}';
    }
}
```
如下代码实现了通过 JDBC 对 tb_student 表的 Select 和 Insert 操作：
```java
private static final String user = "root";
private static final String password = "root";
private static final String URL = "jdbc:mysql://localhost:3306/test?useSSL=false&characterEncoding=utf8";

// 获取数据连接
private static Connection getConnection() throws SQLException {
    // JDBC4 之后不需要再显式通过 Class.forName 注册驱动
    // Class.forName(DRIVER);
    // 获取Connection
    Connection conn = DriverManager.getConnection(URL, user, password);
    return conn;
}

// SELECT：根据姓名查询学生
public static List<Student> findStudentByName(String stuName) {
    List<Student> students = Lists.newArrayList();
    Connection conn = null;
    try {
        // 获得数据库连接
        conn = getConnection();
        // 查询 SQL
        String sql = "SELECT id, stu_id, stu_name, status FROM tb_student where stu_name = ?";
        // 创建 PreparedStatement
        PreparedStatement statement = conn.prepareStatement(sql);
        // 设置输入参数
        statement.setString(1, stuName);
        // 执行查询
        ResultSet rs = statement.executeQuery();
        // 遍历查询结果
        while(rs.next()){
            int id  = rs.getInt("id");
            int stuId = rs.getInt("stu_id");
            int status  = rs.getInt("status");
            // 从数据库中取出结果并生成 Java 对象
            Student stu = new Student();
            stu.setId(id);
            stu.setStuId(stuId);
            stu.setStuName(stuName);
            stu.setStatus(status);
            students.add(stu);
        }
    } catch (SQLException e) {
        throw new RuntimeException(e);
    } finally {
        // 关闭连接
        try {
            if (!Objects.equals(conn, null)) {
                conn.close();
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }
    return students;
}

// INSERT：创建学生
public static int createStudent(Student student) {
    Connection conn = null;
    try {
        // 获得数据库连接
        conn = getConnection();
        // 查询 SQL
        String sql = "INSERT INTO tb_student(stu_id, stu_name, status) VALUES(?,?,?)";
        // 创建 PreparedStatement
        PreparedStatement statement = conn.prepareStatement(sql);
        // 设置输入参数
        statement.setInt(1, student.getStuId());
        statement.setString(2, student.getStuName());
        statement.setInt(3, student.getStatus());
        // 执行更新
        int num = statement.executeUpdate();
        return num;
    } catch (SQLException e) {
        throw new RuntimeException(e);
    } finally {
        // 关闭连接
        try {
            if (!Objects.equals(conn, null)) {
                conn.close();
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }
}
```

> 详细代码请查阅: [MySQLJDBCExample](https://github.com/sjf0115/data-example/blob/master/common-example/src/main/java/com/common/example/jdbc/MySQLJDBCExample.java)

上述的两个方法中有大量的重复代码：获取一个连接，创建一个 Statement 对象，设置输入参数，关闭资源(如 connection)。MyBatis 抽象了上述的这些相同的任务，如准备需要被执行的 SQL Statement 对象并且将 Java 对象作为输入数据传递给 Statement 对象的任务，进而开发人员可以专注于真正重要的方面。另外，MyBatis 自动化了将从输入的 Java 对象中的属性设置成查询参数、从 SQL 结果集上生成 Java 对象这两个过程。

现在让我们看看怎样通过 MyBatis 实现上述的方法。第一步编写 Mapper 接口方法提供按指定名称查询学生以及创建学生的方法：
```java
package com.mybatis.example.mapper;
public interface StudentMapper {
    // 指定根据的名称查询学生
    List<Student> selectByName(@Param("stu_name") String stuName);
    // 创建学生
    int createStudent(Student stu);
}
```
第二步编写 SQL 映射文件，需要注意的是 namespace 命名空间需要与上面的  Mapper 接口路径保持一致(id与方法名称保持一致)，否则在使用 Mapper 代理开发的时候会抛出异常：
```xml
<mapper namespace="com.mybatis.example.mapper.StudentMapper">
    <select id="selectByName" parameterType = "String" resultType="com.mybatis.example.pojo.Student">
        select id, stu_id AS stuId, stu_name AS stuName, status
        from tb_student
        where stu_name = #{stu_name};
    </select>

    <insert id="createStudent" useGeneratedKeys="true" keyProperty="id">
        insert into tb_student (stu_id, stu_name, status)
        values (#{stuId}, #{stuName}, #{status});
    </insert>
</mapper>
```

你可以使用如下代码触发 SQL 语句：
```java
// 加载 Mybatis 的核心配置文件 mybatis-config.xml
String resource = "mybatis-config.xml";
InputStream inputStream = Resources.getResourceAsStream(resource);
SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder().build(inputStream);

SqlSession session = sqlSessionFactory.openSession();
StudentMapper mapper = session.getMapper(StudentMapper.class);

// 插入一个学生
Student stu = new Student();
stu.setStuId(10005);
stu.setStuName("阿尔瓦雷斯");
stu.setStatus(1);
int num = mapper.createStudent(stu);

// 根据指定姓名查询学生
List<Student> students = mapper.selectByName("阿尔瓦雷斯");
for (Student stu : students) {
    System.out.println("查询到的用户结果: " + stu);
}

// 释放资源
session.close();
```
通过上面的代码你可以知道，你不需要创建 Connection 连接，PreparedStatement，不需要自己对每一次数据库操作进行手动设置参数和关闭连接。只需要配置数据库连接属性和 SQL 语句，MyBatis 会处理这些底层工作。

### 2.2 低学习成本

MyBatis 能够流行的首要原因之一在于它学习和使用起来非常简单，它取决于你 Java 和 SQL 方面的知识。如果开发人员很熟悉 Java 和 SQL，他们会发现 MyBatis 入门非常简单。

### 2.3 能够很好地与传统数据库协同工作

有时我们可能需要用不正规形式与传统数据库协同工作，使用成熟的 ORM 框架(如 Hibernate)有可能、但是很难跟传统数据库很好地协同工作，因为他们尝试将 Java 对象静态地映射到数据库的表上。而 MyBatis 是将查询的结果与 Java 对象映射起来，这使得 MyBatis 可以很好地与传统数据库协同工作。你可以根据面相对象的模型创建 Java 域对象，执行传统数据库的查询，然后将结果映射到对应的 Java 对象上。

### 2.4 支持 SQL

成熟的 ORM 框架（如 Hibernate）鼓励使用实体对象（Entity Objects）以及在底层自动产生 SQL 语句。但是这种 SQL 生成策略，使我们不能够充分利用数据库的一些特有特性。Hibernate 允许执行本地 SQL，但是这样会打破持久层和数据独立的原则。

MyBatis 框架接受 SQL 语句，而不是将其对开发人员隐藏起来。由于 MyBatis 不会产生任何的 SQL 语句，所以开发人员需要做好这方面的准备。这样我们既可以充分利用数据库特有的特性并且可以自定义 SQL 查询语句。同时 MyBatis 对存储过程提供了支持。

### 2.5 与 Spring 和 Guice 框架的集成支持

MyBatis 提供了与流行的依赖注入框架 Spring 和 Guice 的开包即用的集成支持，这将进一步简化 MyBatis 的使用。

### 2.6 提供了与第三方缓存类库的集成支持

MyBatis 有内建的 SqlSession 级别的缓存机制，用于缓存 SELECT 语句查询出来的结果。除此之外，MyBatis 提供了与多种第三方缓存类库的集成支持，如 EHCache，OSCache，Hazelcast。

### 2.7 良好的性能

MyBatis 支持数据库连接池，消除了为每一个请求创建一个数据库连接的开销。MyBatis 提供了内建的缓存机制，在 SqlSession 级别提供了对 SQL 查询结果的缓存。如果你调用了相同的 SELECT 查询，MyBatis 会将放在缓存的结果返回，而不会去再查询数据库。MyBatis 框架并没有大量地使用代理机制，因此对于其他的过度地使用代理的 ORM 框架而言，MyBatis 可以获得更好的性能。 

参考：《Java Persistence with MyBatis 3》

​
