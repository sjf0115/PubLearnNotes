## 1. 简介

MyBatis-Generator (mybatis-generator-maven-plugin) 是 MyBatis 提供的快速生成代码的插件。可以帮我们快速生成表对应的持久化对象(POJO)、操作数据库的接口(dao) 以及映射文件 Mapper。

Mybatis-Generator 的运行方式有很多种：
- 基于 mybatis-generator-core-x.x.x.jar 和其 XML 配置文件，通过命令行运行。
- 通过 Ant 的 Task 结合其 XML 配置文件运行。
- 通过 Maven 插件运行。
- 通过 Java 代码和其 XML 配置文件运行。
- 通过 Java 代码和编程式配置运行。
- 通过 Eclipse Feature 运行。

这里只介绍通过 Maven 插件的方式运行，这也是目前最普遍使用的方式。

## 2. 引入插件

如果使用 Maven 插件，那么不需要引入 mybatis-generator-core 依赖，只需要引入一个 Maven 的插件 mybatis-generator-maven-plugin 即可：
```xml
<properties>
    <mybatis.generator.version>1.4.2</mybatis.generator.version>
</properties>

<build>
    <plugins>
        <plugin>
            <groupId>org.mybatis.generator</groupId>
            <artifactId>mybatis-generator-maven-plugin</artifactId>
            <version>${mybatis.generator.version}</version>
        </plugin>
    </plugins>
</build>
```

## 3. 配置插件

光引入 MyBatis Generator 插件还不行，还得需要配置插件。可以通过 configuration 进行配置：
```xml
<build>
    <plugins>
        <plugin>
            <groupId>org.mybatis.generator</groupId>
            <artifactId>mybatis-generator-maven-plugin</artifactId>
            <version>${mybatis.generator.version}</version>
            <!-- 插件配置 -->
            <configuration>
                <!-- 输出详细信息 -->
                <verbose>true</verbose>
                <!-- 覆盖生成文件 -->
                <overwrite>true</overwrite>
                <!-- 定义配置文件 -->
                <configurationFile>${basedir}/src/main/resources/generator-configuration.xml</configurationFile>
            </configuration>
        </plugin>
    </plugins>
</build>
```
所有配置中最重要的就是 `configurationFile`，需要设置一个 xml 配置文件来指定如何生成 DAO 等文件：
```xml
<configurationFile>${basedir}/src/main/resources/generator-configuration.xml</configurationFile>
```
有时候我们的数据库表添加了新字段，需要重新生成对应的文件。你可以手动删除旧文件，然后再用 MyBatis Generator 生成新文件。这比较麻烦，你可以直接让 MyBatis Generator 覆盖旧文件，只需要添加如下配置即可：
```xml
<overwrite>true</overwrite>
```
> 值得注意的是，MyBatis Generator 只会覆盖旧的 po、dao、而映射文件 mapper.xml 不会覆盖，而是追加，这样做的目的是防止用户自己写的 SQL 语句一不小心都被 MyBatis Generator 给覆盖了。

## 4. 添加数据库驱动依赖

MyBatis Generator 需要根据数据表中的字段来生成 DAO 等文件，所以需要添加对应的数据库驱动依赖来连接数据库：
```xml
<properties>
    <mysql.version>5.1.46</mysql.version>
    <mybatis.generator.version>1.4.2</mybatis.generator.version>
</properties>

<build>
    <plugins>
        <plugin>
            <groupId>org.mybatis.generator</groupId>
            <artifactId>mybatis-generator-maven-plugin</artifactId>
            <version>${mybatis.generator.version}</version>

            <!-- 插件配置 -->
            <configuration>
                <!-- 输出详细信息 -->
                <verbose>true</verbose>
                <!-- 覆盖生成文件 -->
                <overwrite>true</overwrite>
                <!-- 定义配置文件 -->
                <configurationFile>${basedir}/src/main/resources/generator-configuration.xml</configurationFile>
            </configuration>

            <!-- 插件依赖 -->
            <dependencies>
                <dependency>
                    <groupId>mysql</groupId>
                    <artifactId>mysql-connector-java</artifactId>
                    <version>${mysql.version}</version>
                </dependency>
            </dependencies>
        </plugin>
    </plugins>
</build>
```
> 在这使用的是 MYSQL 数据库，其他数据库也是一样的配置，需要注意的是数据库驱动的版本号。

在 Web 项目中连接数据库基本是必不可少的操作，所以在大部分情况下，我们的项目中已经配置过了对应数据库的驱动依赖，例如如下所示：
```xml
<properties>
    <mysql.version>5.1.46</mysql.version>
    <mybatis.generator.version>1.4.2</mybatis.generator.version>
</properties>

<dependencies>
    <!-- MySQL 驱动 在父模块中维护版本 -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.mybatis.generator</groupId>
            <artifactId>mybatis-generator-maven-plugin</artifactId>
            <version>${mybatis.generator.version}</version>

            <!-- 插件配置 -->
            <configuration>
                <!-- 输出详细信息 -->
                <verbose>true</verbose>
                <!-- 覆盖生成文件 -->
                <overwrite>true</overwrite>
                <!-- 定义配置文件 -->
                <configurationFile>${basedir}/src/main/resources/generator-configuration.xml</configurationFile>
                <!-- 将当前pom的依赖项添加到生成器的类路径中 -->
                <includeCompileDependencies>true</includeCompileDependencies>
            </configuration>
        </plugin>
    </plugins>
</build>
```
通过上面代码可以看到我们配置了两次 MySQL 驱动，有一些冗余。为此，Maven 提供了 `includeCompileDependencies` 属性，让我们在插件中可以引用上面配置 dependencies 的依赖，这样就不需要重复配置了：
```xml
<properties>
    <mybatis.generator.version>1.4.2</mybatis.generator.version>
</properties>

<dependencies>
    <!-- MySQL 驱动 在父模块中维护版本 -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.mybatis.generator</groupId>
            <artifactId>mybatis-generator-maven-plugin</artifactId>
            <version>${mybatis.generator.version}</version>

            <!-- 插件配置 -->
            <configuration>
                <!-- 输出详细信息 -->
                <verbose>true</verbose>
                <!-- 覆盖生成文件 -->
                <overwrite>true</overwrite>
                <!-- 定义配置文件 -->
                <configurationFile>${basedir}/src/main/resources/generator-configuration.xml</configurationFile>
                <!-- 将当前pom的依赖项添加到生成器的类路径中 -->
                <includeCompileDependencies>true</includeCompileDependencies>
            </configuration>
        </plugin>
    </plugins>
</build>
```
如果你不想在 MyBatis Generator 插件中使用上面 dependencies 配置的版本，而是想使用另一个版本的依赖，也可以配置插件的 dependencies。

> 如果你配置了 mybatis-generator-maven-plugin 插件，就不需要在插件中配置 mybatis-generator-core 依赖了。

## 5. 配置 XML 配置文件

MyBatis Generator 插件启动后，会根据你在 pom 中 `configurationFile` 配置的路径找到 XML 配置文件。该 XML 配置文件是 Mybatis Generator 的核心，用于控制代码生成的所有行为。

XML 配置文件最外层的标签为 `<generatorConfiguration>`，子标签包括：
- 0 或者 1 个 `<properties>` 标签，用于指定全局配置文件，后面可以通过占位符的形式读取 `<properties>` 指定文件中的值。
- 0 或者 N 个 `<classPathEntry>` 标签，`<classPathEntry>` 只有一个 location 属性，用于指定数据源驱动包（jar或者zip）的绝对路径，具体选择什么驱动包取决于连接什么类型的数据源。
- 1 或者 N 个 `<context>` 标签，用于运行时的解析模式和具体的代码生成行为，所以这个标签里面的配置是最重要的。

在这我们配置了 1 个 `<properties>` 标签来引入 JDBC 配置。此外最重要的就是配置一个 `<context>` 标签：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE generatorConfiguration
        PUBLIC "-//mybatis.org//DTD MyBatis Generator Configuration 1.0//EN"
        "http://mybatis.org/dtd/mybatis-generator-config_1_0.dtd">

<generatorConfiguration>
    <!--  引入 JDBC 配置 -->
    <properties resource="jdbc.properties"/>

    <context id="default" targetRuntime="MyBatis3" defaultModelType="flat">
      ...
    </context>
</generatorConfiguration>
```

### 5.1 配置 properties

通过 properties 标签引入 jdbc.properties 配置文件中的 JDBC 配置：
```xml
<properties resource="jdbc.properties"/>
```
例如配置文件中的内容如下所示：
```xml
jdbc.user=root
jdbc.password=root
jdbc.driverClass=com.mysql.jdbc.Driver
jdbc.jdbcUrl=jdbc:mysql://localhost:3306/test?useSSL=false&amp;characterEncoding=utf8
```
在 context 标签中配置 jdbcConnection 时，可以通过 `${xxx}` 来引用 JDBC 配置文件中的值，如下所示：
```xml
<!--数据库链接URL，用户名、密码 -->
<jdbcConnection driverClass="${jdbc.driverClass}"
                connectionURL="${jdbc.jdbcUrl}"
                userId="${jdbc.user}"
                password="${jdbc.password}">
</jdbcConnection>
```

### 5.2 配置 context

```xml
<context id="myContext" targetRuntime="MyBatis3" defaultModelType="flat">

</context>
```

`<context>` 标签除了有大量的子标签配置之外，也需要配置几个比较主要的属性：
- id：Context 实例的唯一ID，用于输出错误信息时候作为唯一标记。这个值可以随便填，只需要保证多个 id 不重复即可
- defaultModelType：可以不填，默认值为 conditional，flat 表示一张表对应一个 po
- targetRuntime：用于执行代码生成模式。可以不填，默认值 MyBatis3。常用的还有 MyBatis3Simple，这个配置会影响 dao 等内容的生成

下面具体说一下 context 标签下的几个比较重要的子标签：
```xml
<context id="default" targetRuntime="MyBatis3" defaultModelType="flat">

    <commentGenerator>
        <!-- 这个元素用来去除指定生成的注释中是否包含生成的日期 false:表示保护 -->
        <!-- 如果生成日期，会造成即使修改一个字段，整个实体类所有属性都会发生变化，不利于版本控制，所以设置为true -->
        <property name="suppressDate" value="true"/>
        <!-- 是否排除自动生成的注释 true：是 ： false:否 -->
        <property name="suppressAllComments" value="true"/>
    </commentGenerator>

    <!--数据库链接URL，用户名、密码 -->
    <jdbcConnection driverClass="${jdbc.driverClass}"
                    connectionURL="${jdbc.jdbcUrl}"
                    userId="${jdbc.user}"
                    password="${jdbc.password}">
    </jdbcConnection>

    <javaTypeResolver>
        <property name="forceBigDecimals" value="false"/>
    </javaTypeResolver>

    <!-- 生成模型的包名和位置 -->
    <javaModelGenerator targetPackage="com.spring.example.model" targetProject="./src/main/generated-sources">
        <property name="enableSubPackages" value="true" />
        <property name="trimStrings" value="true" />
    </javaModelGenerator>

    <!-- 生成映射文件的包名和位置 -->
    <sqlMapGenerator targetPackage="com.spring.example.mapper" targetProject="./src/main/generated-sources">
        <property name="enableSubPackages" value="true" />
    </sqlMapGenerator>

    <!-- 生成DAO的包名和位置 -->
    <javaClientGenerator type="XMLMAPPER"
                         targetPackage="com.spring.example.dao"
                         targetProject="./src/main/generated-sources">
        <property name="enableSubPackages" value="true" />
    </javaClientGenerator>

    <!-- 要生成哪些表 -->
    <table tableName="tb_book" domainObjectName="Book"
           enableCountByExample="false"
           enableUpdateByExample="false"
           enableDeleteByExample="false"
           enableSelectByExample="false"
           selectByExampleQueryId="false"></table>

</context>
```
在配置该标签时，你需要注意的是 context 的子标签必须按照如下给出的个数以及顺序配置，即 MyBatis Generator 对配置的个数和循序是有要求的：
- property：0 或者 N 个
- plugin：0 或者 N 个
- commentGenerator：0 或者 1 个
- jdbcConnection：connectionFactory 或者 jdbcConnection
- javaTypeResolver：0 或者 1 个
- javaModelGenerator：1 个
- sqlMapGenerator：0 或者 1 个
- javaClientGenerator：0 或者 1 个
- table：1 或者 N 个

> property*,plugin*,commentGenerator?,(connectionFactory|jdbcConnection),javaTypeResolver?,javaModelGenerator,sqlMapGenerator?,javaClientGenerator?,table+。

下面介绍几个比较常用的标签。

#### 5.2.1 commentGenerator

commentGenerator 用来配置生成的注释。默认是生成注释的，并且会生成时间戳，如下所示：
```java
public interface BookMapper {
    /**
     * This method was generated by MyBatis Generator.
     * This method corresponds to the database table tb_book
     *
     * @mbg.generated Mon Jul 24 08:21:38 CST 2023
     */
    int deleteByPrimaryKey(Integer id);
    ...
}
```
如果你不想保留时间戳，需要如下配置：
```xml
<commentGenerator>
    <!-- 是否排除自动生成的注释 true：是 ： false:否 -->
    <property name="suppressAllComments" value="true"/>
</commentGenerator>
```

#### 5.2.2 jdbcConnection

MyBatis Generator 需要链接数据库，所以需要配置 jdbcConnection，具体配置如下所示：
```xml
<!--数据库链接URL，用户名、密码 -->
<jdbcConnection driverClass="${jdbc.driverClass}"
                connectionURL="${jdbc.jdbcUrl}"
                userId="${jdbc.user}"
                password="${jdbc.password}">
</jdbcConnection>
```
在上面讲解 properties 标签时已经提及到可以通过 `${xxx}` 占位符来引用 JDBC 配置文件中的值。

`<jdbcConnection>` 标签用于指定数据源的连接信息，其中 driverClass 是数据源驱动的全类名、connectionURL 是 JDBC 的连接 URL、userId 是连接到数据源的用户名、password 是连接到数据源的密码。

#### 5.2.3 javaTypeResolver

javaTypeResolver 是配置 JDBC 与 java 的类型转换规则，或者你也可以不用配置，使用它默认的转换规则。

就算配置也只能配置 bigDecimal 类型和时间类型的转换

<javaTypeResolver>
    <property name="forceBigDecimals" value="false"/>
</javaTypeResolver>





...
