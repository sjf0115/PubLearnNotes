## 1. 背景

在开发 Spring MVC 项目通过 Json 传递参数时需要引入 jackson-databind 坐标：
```xml
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.13.5</version>
</dependency>
```

引入坐标启动 Tomcat 后抛出如下异常：
```java
严重: Unable to process Jar entry [META-INF/versions/9/module-info.class] from Jar [jar:file:.../repository/com/fasterxml/jackson/core/jackson-databind/2.13.5/jackson-databind-2.13.5.jar!/] for annotations
org.apache.tomcat.util.bcel.classfile.ClassFormatException: Invalid byte tag in constant pool: 19
	at org.apache.tomcat.util.bcel.classfile.Constant.readConstant(Constant.java:133)
	at org.apache.tomcat.util.bcel.classfile.ConstantPool.<init>(ConstantPool.java:60)
	at org.apache.tomcat.util.bcel.classfile.ClassParser.readConstantPool(ClassParser.java:209)
	at org.apache.tomcat.util.bcel.classfile.ClassParser.parse(ClassParser.java:119)
	at org.apache.catalina.startup.ContextConfig.processAnnotationsStream(ContextConfig.java:2105)
	at org.apache.catalina.startup.ContextConfig.processAnnotationsJar(ContextConfig.java:1981)
	at org.apache.catalina.startup.ContextConfig.processAnnotationsUrl(ContextConfig.java:1947)
	at org.apache.catalina.startup.ContextConfig.processAnnotations(ContextConfig.java:1932)
	at org.apache.catalina.startup.ContextConfig.webConfig(ContextConfig.java:1326)
	at org.apache.catalina.startup.ContextConfig.configureStart(ContextConfig.java:878)
	at org.apache.catalina.startup.ContextConfig.lifecycleEvent(ContextConfig.java:369)
	at org.apache.catalina.util.LifecycleSupport.fireLifecycleEvent(LifecycleSupport.java:119)
	at org.apache.catalina.util.LifecycleBase.fireLifecycleEvent(LifecycleBase.java:90)
	at org.apache.catalina.core.StandardContext.startInternal(StandardContext.java:5179)
	at org.apache.catalina.util.LifecycleBase.start(LifecycleBase.java:150)
	at org.apache.catalina.core.ContainerBase$StartChild.call(ContainerBase.java:1559)
	at org.apache.catalina.core.ContainerBase$StartChild.call(ContainerBase.java:1549)
	at java.util.concurrent.FutureTask.run(FutureTask.java:266)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:748)
```

## 2. 解决方案

通过上面的代码很容易发现是 Tomcat 和 Jackson 不兼容导致的。在这我们使用的是 Tomcat 插件：
```xml
<build>
    <plugins>
        <!-- Tomcat7 插件-->
        <plugin>
            <groupId>org.apache.tomcat.maven</groupId>
            <artifactId>tomcat7-maven-plugin</artifactId>
            <!-- 插件配置 -->
            <configuration>
                <port>8070</port>
                <path>/</path>
                <uriEncoding>UTF-8</uriEncoding>
            </configuration>
        </plugin>
    </plugins>
</build>
```
根本原因是 Tomcat 插件的版本过低，jackson-databind 版本过高，导致 tomcat 和 jackson-databind 发生冲突。

### 2.1 降低 jackson-databind 版本

jackson-databind 版本过高，那么通过降低 jackson-databind 的版本来解决：
```xml
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.9.8</version>
</dependency>
```
### 2.2 scope 指定 provided

在 pom.xml 文件导入 jackson-databind 依赖时 scope 指定 provided，让 jackson-databind 依赖只在编译时有效。
```xml
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.13.5</version>
    <scope>provided</scope>
</dependency>
```

### 2.3 升级 Tomcat

tomcat7-maven-plugin 插件最新版本是 2.2，默认运行 7.0.47 的 Tomcat，在这升级到 7.0.86：
```xml
<properties>
    <tomcat.version>7.0.86</tomcat.version>
</properties>

<build>
    <plugins>
        <!-- Tomcat7 插件-->
        <plugin>
            <groupId>org.apache.tomcat.maven</groupId>
            <artifactId>tomcat7-maven-plugin</artifactId>
            <!-- 插件配置 -->
            <configuration>
                <port>8070</port>
                <path>/</path>
                <uriEncoding>UTF-8</uriEncoding>
            </configuration>

            <dependencies>
                <dependency>
                    <groupId>org.apache.tomcat.embed</groupId>
                    <artifactId>tomcat-embed-core</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>
                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-util</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>
                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-coyote</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>
                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-api</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-jdbc</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-dbcp</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-servlet-api</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-jsp-api</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-jasper</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-jasper-el</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-el-api</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-catalina</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-tribes</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-catalina-ha</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-annotations-api</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat</groupId>
                    <artifactId>tomcat-juli</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>

                <dependency>
                    <groupId>org.apache.tomcat.embed</groupId>
                    <artifactId>tomcat-embed-logging-juli</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>
                <dependency>
                    <groupId>org.apache.tomcat.embed</groupId>
                    <artifactId>tomcat-embed-logging-log4j</artifactId>
                    <version>${tomcat.version}</version>
                </dependency>
            </dependencies>
        </plugin>
    </plugins>
</build>
```
> 你也可以尝试使用 tomcat8-maven-plugin 插件
