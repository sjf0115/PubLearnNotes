


## 1.

需要下载核心的包，core 与 common，使用 Maven 安装到本地仓库：
```
mvn install:install-file -DgroupId=com.datax -DartifactId=datax-core -Dversion=1.0.0 -Dpackaging=jar -Dfile=/opt/workspace/datax/lib/datax-core-0.0.1-SNAPSHOT.jar

mvn install:install-file -DgroupId=com.datax -DartifactId=datax-common -Dversion=1.0.0 -Dpackaging=jar -Dfile=/opt/workspace/datax/lib/datax-common-0.0.1-SNAPSHOT.jar
```

![]()


## 2. 依赖

```xml
<!-- SpringBoot工程需要继承的父工程 -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.5</version>
    <relativePath/>
</parent>

<artifactId>spring-boot-datax</artifactId>
<packaging>jar</packaging>

<properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <lombok.version>1.18.26</lombok.version>
    <datax.version>1.0.0</datax.version>
</properties>

<dependencies>
    <!-- Web开发需要的起步依赖 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- DataX -->
    <dependency>
        <groupId>com.datax</groupId>
        <artifactId>datax-common</artifactId>
        <version>${datax.version}</version>
    </dependency>

    <dependency>
        <groupId>com.datax</groupId>
        <artifactId>datax-core</artifactId>
        <version>${datax.version}</version>
    </dependency>

    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <version>${lombok.version}</version>
    </dependency>
</dependencies>
```
