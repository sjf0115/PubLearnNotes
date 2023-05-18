MyBatis 的真正强大在于它的语句映射，这是它的魔力所在。由于它的异常强大，映射器的 XML 文件就显得相对简单。如果拿它跟具有相同功能的 JDBC 代码进行对比，你会立即发现省掉了将近 95% 的代码。MyBatis 致力于减少使用成本，让用户能更专注于 SQL 代码。

SQL 映射文件只有很少的几个顶级元素（按照应被定义的顺序列出）：
cache – 该命名空间的缓存配置。
cache-ref – 引用其它命名空间的缓存配置。
resultMap – 描述如何从数据库结果集中加载对象，是最复杂也是最强大的元素。
parameterMap – 老式风格的参数映射。此元素已被废弃，并可能在将来被移除！请使用行内参数映射。文档中不会介绍此元素。
sql – 可被其它语句引用的可重用语句块。
insert – 映射插入语句。
update – 映射更新语句。
delete – 映射删除语句。
select – 映射查询语句。


```sql
-- 删除tb_student表
drop table if exists tb_student;
-- 创建tb_student表
create table tb_student (
    -- id 主键
    id int primary key auto_increment,
    stu_id int comment '学生编号',
    stu_name varchar(20) comment '学生姓名',
    status int comment '状态：0:删除, 1:未删除'
);

-- 添加数据
insert into tb_brand (stu_id, stu_name, status) values
  ('10001', '梅西', 1),
  ('10002', 'C罗', 1),
  ('10003', '哈兰德', 1);
```


## 1. 查询:SELECT

查询语句是 MyBatis 中最常用的元素之一。如果只是把数据存到数据库中价值并不大，还需要能重新取出来才能发挥更大的价值。对于大多数应用也都是查询比修改要频繁。MyBatis 的基本原则之一是：在每个插入、更新或删除操作之间，通常会执行多个查询操作。因此，MyBatis 在查询和结果映射做了相当多的改进。一个简单查询的 SELECT 元素是非常简单的。例如，在 [MyBatis 快速入门](https://smartsi.blog.csdn.net/article/details/130717598)中介绍的根据指定 Id 查询用的语句：
```xml
<!-- 根据指定的 Id 查询用户 -->
<select id="selectById" resultType="com.mybatis.example.pojo.User">
    SELECT * FROM tb_user WHERE id = #{id};
</select>
```
这个语句名为 `selectById`，接受一个用户 Id 的参数，并返回一个 POJO 类型的 User 对象，其中的键是列名，值便是结果行中的对应值。需要注意的是参数符号：
```
#{id}
```
这就告诉 MyBatis 创建一个预处理语句（PreparedStatement）参数，在 JDBC 中，这样的一个参数在 SQL 中会由一个 `?` 来标识，并被传递到一个新的预处理语句中，就像这样：
```java
// 近似的 JDBC 代码，非 MyBatis 代码...
String selectPerson = "SELECT * FROM tb_user WHERE id = ?";
PreparedStatement ps = conn.prepareStatement(selectPerson);
ps.setInt(1,id);
```

### 1.1 SELECT 元素

SELECT 元素允许你配置很多属性来配置每条语句的行为细节：
```xml
<select
  id="selectById"
  parameterType="int"
  resultType="com.mybatis.example.pojo.User"
  flushCache="false"
  useCache="true"
  timeout="10"
  fetchSize="256"
  statementType="PREPARED"
  resultSetType="FORWARD_ONLY">
```

| 属性     | 描述     |
| :------------- | :------------- |
| id       | 在命名空间中唯一的标识符，可以被用来引用这条语句 |
| parameterType	| 传入参数的类全限定名或别名(例如，`int`)。这个属性是可选的，因为 MyBatis 可以通过类型处理器（TypeHandler）推断出具体传入的参数，默认值为未设置（unset）|
| resultType	| 期望从这条语句中返回结果的类全限定名或别名。如果返回的是集合，设置为集合中元素的类型，而不是集合本身的类型。resultType 和 resultMap 之间只能同时使用一个 |
| resultMap	| 用于结果的映射。对外部 resultMap 的命名引用。resultType 和 resultMap 之间只能同时使用一个。|
| flushCache | 设置为 true 后，只要语句被调用，都会导致本地缓存和二级缓存被清空，默认值：false。|
| useCache | 设置为 true 后，将会导致本条语句的结果被二级缓存缓存起来，默认值：对 select 元素为 true。|
| timeout	| 这个设置是在抛出异常之前，驱动程序等待数据库返回请求结果的秒数。默认值为未设置（unset）（依赖数据库驱动）。|
| fetchSize	| 这是一个给驱动的建议值，尝试让驱动程序每次批量返回的结果行数等于这个设置值。 默认值为未设置（unset）（依赖驱动）。|
| statementType	| 可选 STATEMENT，PREPARED 或 CALLABLE。这会让 MyBatis 分别使用 Statement，PreparedStatement 或 CallableStatement，默认值：PREPARED。|
| resultSetType	| FORWARD_ONLY，SCROLL_SENSITIVE, SCROLL_INSENSITIVE 或 DEFAULT（等价于 unset） 中的一个，默认值为 unset （依赖数据库驱动）。|
| databaseId	| 如果配置了数据库厂商标识（databaseIdProvider），MyBatis 会加载所有不带 databaseId 或匹配当前 databaseId 的语句；如果带和不带的语句都有，则不带的会被忽略。|
| resultOrdered	| 这个设置仅针对嵌套结果 select 语句：如果为 true，将会假设包含了嵌套结果集或是分组，当返回一个主结果行时，就不会产生对前面结果集的引用。这就使得在获取嵌套结果集的时候不至于内存不够用。默认值：false。|
| resultSets | 这个设置仅适用于多结果集的情况。它将列出语句执行后返回的结果集并赋予每个结果集一个名称，多个名称之间以逗号分隔。|

### 1.2 示例

第一步编写 Mapper 接口方法，如下提供了查询所有学生以及根据指定 ID 查询学生的方法：
```java
package com.mybatis.example.mapper;
public interface StudentMapper {
    List<Student> selectAll();
    Student selectById(@Param("stu_id") int id);
}
```
第二步编写 SQL 映射文件，需要注意的是 namespace 命名空间需要与上面的  Mapper 接口路径保持一致(id与方法名称保持一致)，否则在使用 Mapper 代理开发的时候会抛出异常：
```xml
<mapper namespace="com.mybatis.example.mapper.StudentMapper">
    <select id="selectAll" parameterType = "int" resultType="com.mybatis.example.pojo.Student">
        select * from tb_student;
    </select>

    <select id="selectById" parameterType = "int" resultType="com.mybatis.example.pojo.Student">
        select * from tb_student where stu_id = #{stu_id};
    </select>
</mapper>
```

第三步编写执行方法：
```java
public class SelectStudent {
    public static void main(String[] args) throws IOException {
        // 加载 Mybatis 的核心配置文件 mybatis-config.xml
        String resource = "mybatis-config.xml";
        InputStream inputStream = Resources.getResourceAsStream(resource);
        SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder().build(inputStream);

        SqlSession session = sqlSessionFactory.openSession();

        // 查询所有的学生
        StudentMapper mapper = session.getMapper(StudentMapper.class);
        List<Student> students = mapper.selectAll();
        for (Student stu : students) {
            System.out.println("全部学生: " + stu);
        }

        // 根据指定的ID查询学生
        Student student = mapper.selectById(10001);
        System.out.println("目标学生: " + student);

        // 释放资源
        session.close();
    }
}
```
根据上面的执行方法输出如下信息，但是我们发现学生的 id 为 0、姓名 为 'null'：
```
全部学生: Student{id=1, stuId=0, stuName='null', status=1}
目标学生: Student{id=1, stuId=0, stuName='null', status=1}
```
这一问题的主要原因是学生编号和姓名两个字段在数据库(stu_id、stu_name)和 POJO 类(sutId、stuName)中命名不一致，才导致不能自动封装数据。针对这一问题，在这提供了两种解决方案，需要修改 XML Mapper：
- 对不一致的列名起别名，与实体类保持一致
- 使用 ResultMap 进行映射

为了演示两种方式，查询所有的用户使用的是第一种方式，根据指定的 Id 查询用户使用的是第二种方式
```xml
<mapper namespace="com.mybatis.example.mapper.StudentMapper">
    <!-- 1 查询所有的用户 使用别名方式 -->
    <select id="selectAll" parameterType = "int" resultType="com.mybatis.example.pojo.Student">
        select id, stu_id AS stuId, stu_name AS stuName, status
        from tb_student;
    </select>

    <!-- 2 根据指定的 Id 查询用户 使用 ResultMap 进行映射方式 -->
    <resultMap id="studentResultMap" type="com.mybatis.example.pojo.Student">
        <result column="stu_id" property="stuId"/>
        <result column="stu_name" property="stuName"/>
    </resultMap>

    <select id="selectById" parameterType = "int" resultMap="studentResultMap">
        select * from tb_student where stu_id = #{stu_id};
    </select>
</mapper>
```
经过上述修改之后输出如下正确信息：
```
全部学生: Student{id=1, stuId=10001, stuName='梅西', status=1}
目标学生: Student{id=1, stuId=10001, stuName='梅西', status=1}
```

## 2. 插入:INSERT

### 2.1 INSERT 元素

```xml
<insert
  id="insertAuthor"
  parameterType="domain.blog.Author"
  flushCache="true"
  statementType="PREPARED"
  keyProperty=""
  keyColumn=""
  useGeneratedKeys=""
  timeout="20">
```

| 属性     | 描述     |
| :------------- | :------------- |
| id       | 在命名空间中唯一的标识符，可以被用来引用这条语句 |
| parameterType	| 传入参数的类全限定名或别名。这个属性是可选的，因为 MyBatis 可以通过类型处理器（TypeHandler）推断出具体传入的参数，默认值为未设置（unset）|
| flushCache | 将其设置为 true 后，只要语句被调用，都会导致本地缓存和二级缓存被清空，默认值：false。|
| statementType	| 可选 STATEMENT，PREPARED 或 CALLABLE。这会让 MyBatis 分别使用 Statement，PreparedStatement 或 CallableStatement，默认值：PREPARED。|
| useGeneratedKeys | 会令 MyBatis 使用 JDBC 的 getGeneratedKeys 方法来取出由数据库内部生成的主键（比如：像 MySQL 和 SQL Server 这样的关系型数据库管理系统的自动递增字段），默认值：false。|
| keyProperty	| 指定能够唯一识别对象的属性，MyBatis 会使用 getGeneratedKeys 的返回值或 insert 语句的 selectKey 子元素设置它的值，默认值：未设置（unset）。如果生成列不止一个，可以用逗号分隔多个属性名称。 |
| keyColumn	| 设置生成键值在表中的列名，在某些数据库（像 PostgreSQL）中，当主键列不是表中的第一列的时候，是必须设置的。如果生成列不止一个，可以用逗号分隔多个属性名称。|
| timeout	| 这个设置是在抛出异常之前，驱动程序等待数据库返回请求结果的秒数。默认值为未设置（unset）（依赖数据库驱动）。|


首先，如果你的数据库支持自动生成主键（比如 MySQL 和 SQL Server），那么你可以设置 `useGeneratedKeys='true'`，然后再把 `keyProperty` 设置为目标属性即可。例如，如果上面的 Author 表已经在 id 列上使用了自动生成，那么语句可以修改为：
```xml
<insert id="insertAuthor" useGeneratedKeys="true" keyProperty="id">
  insert into Author (username,password,email,bio)
  values (#{username},#{password},#{email},#{bio})
</insert>
```
如果你的数据库还支持多行插入, 你也可以传入一个 Author 数组或集合，并返回自动生成的主键：
```xml
<insert id="insertAuthor" useGeneratedKeys="true" keyProperty="id">
  insert into Author (username, password, email, bio) values
  <foreach item="item" collection="list" separator=",">
    (#{item.username}, #{item.password}, #{item.email}, #{item.bio})
  </foreach>
</insert>
```

### 2.2 示例

第一步编写 Mapper 接口方法，如下提供了插入一个学生的方法：
```java
package com.mybatis.example.mapper;
public interface StudentMapper {
    // 插入
    void addStudent(Student stu);
}
```
第二步编写 SQL 映射文件，需要注意的是 namespace 命名空间需要与上面的  Mapper 接口路径保持一致(id与方法名称保持一致)，否则在使用 Mapper 代理开发的时候会抛出异常：
```xml
<mapper namespace="com.mybatis.example.mapper.StudentMapper">
    <!-- 插入 -->
    <insert id="addStudent" useGeneratedKeys="true" keyProperty="id">
        insert into tb_student (stu_id, stu_name, status)
        values (#{stuId}, #{stuName}, #{status});
    </insert>
</mapper>
```

第三步编写执行方法：
```java
public class InsertStudent {
    public static void main(String[] args) throws IOException {
        // 加载 Mybatis 的核心配置文件 mybatis-config.xml
        String resource = "mybatis-config.xml";
        InputStream inputStream = Resources.getResourceAsStream(resource);
        SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder().build(inputStream);

        SqlSession session = sqlSessionFactory.openSession();

        StudentMapper mapper = session.getMapper(StudentMapper.class);

        // 插入一个学生
        Student stu = new Student();
        stu.setStuId(10002);
        stu.setStuName("C罗");
        stu.setStatus(1);
        mapper.addStudent(stu);

        // 释放资源
        session.close();
    }
}
```
根据上面的执行方法输出如下信息，同时查询数据库并没有插入这一条记录：
```java
[DEBUG]  [main] o.a.i.t.j.JdbcTransaction - Opening JDBC Connection
[DEBUG]  [main] o.a.i.d.p.PooledDataSource - Created connection 558187323.
[DEBUG]  [main] o.a.i.t.j.JdbcTransaction - Setting autocommit to false on JDBC Connection [com.mysql.jdbc.JDBC4Connection@2145433b]
[DEBUG]  [main] c.m.e.m.S.addStudent - ==>  Preparing: insert into tb_student (stu_id, stu_name, status) values (?, ?, ?);
[DEBUG]  [main] c.m.e.m.S.addStudent - ==> Parameters: 10002(Integer), C罗(String), 1(Integer)
[DEBUG]  [main] c.m.e.m.S.addStudent - <==    Updates: 1
[DEBUG]  [main] o.a.i.t.j.JdbcTransaction - Rolling back JDBC Connection [com.mysql.jdbc.JDBC4Connection@2145433b]
[DEBUG]  [main] o.a.i.t.j.JdbcTransaction - Resetting autocommit to true on JDBC Connection [com.mysql.jdbc.JDBC4Connection@2145433b]
[DEBUG]  [main] o.a.i.t.j.JdbcTransaction - Closing JDBC Connection [com.mysql.jdbc.JDBC4Connection@2145433b]
[DEBUG]  [main] o.a.i.d.p.PooledDataSource - Returned connection 558187323 to pool.
```
从日志中可以发现在开启事务时关闭了自动提交功能(`Setting autocommit to false`)，即需要我们手动提交来完成插入。但这上面代码中我们没有提交事务，虽然执行了插入 SQL，但是事务帮我们进行了回滚(`Rolling back`)。针对这一问题，有两种解决方案：
- 可以手动提交事务，即在完成插入 SQL 语句执行后调用 `session.commit()`
- 可以在获取 SqlSession 时设置自动提交事务 `SqlSession session = sqlSessionFactory.openSession(true)`

如下所示在获取 SqlSession 时设置了自动提交事务：
```java
public class InsertStudent {
    public static void main(String[] args) throws IOException {
        // 加载 Mybatis 的核心配置文件 mybatis-config.xml
        String resource = "mybatis-config.xml";
        InputStream inputStream = Resources.getResourceAsStream(resource);
        SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder().build(inputStream);

        // 获取 SqlSession 并开启自动事务提交
        SqlSession session = sqlSessionFactory.openSession(true);

        StudentMapper mapper = session.getMapper(StudentMapper.class);

        // 插入一个学生
        Student stu = new Student();
        stu.setStuId(10002);
        stu.setStuName("C罗");
        stu.setStatus(1);
        mapper.addStudent(stu);

        // 释放资源
        session.close();
    }
}
```
执行完之后再查看数据库发现数据已经插入成功了。


## 3. 更新:UPDATE

```xml
<update
  id="updateAuthor"
  parameterType="domain.blog.Author"
  flushCache="true"
  statementType="PREPARED"
  timeout="20">
```


## 4. 删除:DELETE

```xml
<delete
  id="deleteAuthor"
  parameterType="domain.blog.Author"
  flushCache="true"
  statementType="PREPARED"
  timeout="20">
```
