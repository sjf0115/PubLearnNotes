## 1. 问题

在执行 MyBatis [快速入门项目](https://github.com/sjf0115/spring-example/blob/main/mybatis-quick-start/src/main/java/com/mybatis/example/MybatisQuickStartMapper.java)时抛出如下异常：
```
Exception in thread "main" org.apache.ibatis.binding.BindingException: Type interface com.mybatis.example.mapper.UserMapper is not known to the MapperRegistry.
	at org.apache.ibatis.binding.MapperRegistry.getMapper(MapperRegistry.java:47)
	at org.apache.ibatis.session.Configuration.getMapper(Configuration.java:876)
	at org.apache.ibatis.session.defaults.DefaultSqlSession.getMapper(DefaultSqlSession.java:288)
	at com.mybatis.example.MybatisQuickStartMapper.main(MybatisQuickStartMapper.java:32)
```

## 2. 解决方案

上述异常信息的出现一般是因为 `mybatis-config.xml` 的 mapper 的配置出错了，无法找到相应的 UserMapper 接口的 UserMapper.xml 的映射文件：
```xml
<mappers>
     <mapper resource="UserMapper.xml"/>
</mappers>
```
通过 `mybatis-config.xml` 核心配置文件可以知道需要在 resource 根目录下有一个 `UserMapper.xml` 配置文件，检查发现没有问题。查看 `UserMapper.xml` 配置文件，命名空间为 `com.mybatis.example.UserMapper`：
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

    <!-- 根据指定的 Id 查询用户 -->
    <select id="selectById" resultType="com.mybatis.example.pojo.User">
        select * from tb_user where id = #{id};
    </select>
</mapper>
```
发现命名空间与我们 UserMapper 接口的包路径 `com.mybatis.example.mapper.UserMapper` 不一致，所以才导致上述异常的出现。如果要使用 Mapper 代理开发必须满足 `设置 SQL 映射文件的 namespace 属性为 Mapper 接口全限定名` 的要求。详细请查阅[Mybatis 快速入门](https://smartsi.blog.csdn.net/article/details/130717598)。
