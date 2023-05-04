DataStream 作业开发时往往会遇到一些 jar 包冲突等问题，本文主要讲解作业开发时需要引入哪些依赖以及哪些需要被打包进作业的 jar 中，从而避免不必要的依赖被打入了作业 jar 中以及可能产生的依赖冲突。

## 1. 核心依赖

每一个 Flink 应用程序都依赖于一系列相关的库，其中至少应该包括 Flink 的 API。许多应用程序还依赖于连接器 Connector 相关的库(比如 Kafka,、Cassandra等)。在运行 Flink 应用程序时，无论是在运行在分布式的环境下还是在本地 IDE 进行测试，Flink 的运行时相关依赖都是必须的。

与大多数运行用户自定义应用程序的系统一样，Flink 中有两大类依赖项：
- Flink 核心依赖
  - Flink 本身由一组运行系统所必需的类和依赖项组成，例如协调器、网络、检查点、容错、API、算子（例如窗口）、资源管理等。 所有这些类和依赖项的集合构成了 Flink 运行时的核心，在 Flink 应用程序启动时必须存在。这些核心类和依赖项都被打包在 flink-dist jar 中。它们是 Flink 的 lib 文件夹的一部分，也是 Flink 基础容器镜像的一部分。这些依赖之于 Flink 就像 Java 运行所需的包含 String 和 List 等类的核心库（rt.jar、charsets.jar 等）之于 Java。Flink 的核心依赖不包含任何连接器或扩展库（CEP、SQL、ML等），这使得 Flink 的核心依赖尽可能小，以避免默认情况下类路径中有过多的依赖项，同时减少依赖冲突。
- 用户应用程序依赖项
  - 指特定用户应用程序所需的所有连接器、Format 或扩展库。用户应用程序通常被打包成一个 jar 文件，其中包含应用程序代码以及所需的连接器和库依赖项。用户应用程序依赖项不应包括 Flink DataStream API 和运行时依赖项，因为这些已经被包含在了 Flink 的核心依赖中。

## 2. 依赖配置

### 2.1 添加基础依赖

每一个 Flink 应用程序的开发至少需要添加相关 API 的基础依赖。手动配置项目时，需要添加 Java/Scala API 的依赖(这里以 Maven 为例，在其他构建工具(Gradle，SBT等)中可以使用同样的依赖)：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-streaming-java_2.11</artifactId>
  <version>1.12.3</version>
  <scope>provided</scope>
</dependency>
```

> 需要注意的是，所有这些依赖项都将其范围设置为 `provided`。这意味着需要对它们进行编译，但不应将它们打包到项目生成的应用程序 jar 文件中。这些依赖项是 Flink 核心依赖项，在实际运行时已经被加载。

强烈建议将依赖项设置成 `provided` 的范围，如果未将它们设置为 `provided`，最好的情况下会导致生成的 jar 变得臃肿，因为它还包含所有 Flink 核心依赖项。而最怀的情况下，添加到应用程序 jar 文件中的 Flink 核心依赖项与您自己的一些依赖项会发生版本冲突（通常通过 Flink 的反向类加载机制来避免）。

> 关于 IntelliJ 的注意事项：为了使应用程序在 IntelliJ IDEA 中运行，有必要在运行配置中勾选 `Include dependencies with "Provided" scope` 选项框。如果没有该选项（可能是由于使用较旧的 IntelliJ IDEA 版本），那么一个简单的解决方法是创建一个调用应用程序 main() 方法的测试用例。

### 2.2 添加连接器和库的依赖

大多数应用程序的运行需要特定的连接器或库，例如 Kafka、Cassandra 等连接器。这些连接器不是 Flink 核心依赖项的一部分，必须作为额外依赖项添加到应用程序中。下述代码是添加 Kafka 连接器依赖项的示例（Maven语法）：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-connector-kafka_2.11</artifactId>
    <version>1.12.3</version>
</dependency>
```
我们建议将应用程序代码和它所有的依赖以 `jar-with-dependencies` 的形式打包到一个 application jar 中。这个应用程序 jar 包可以被提交到已经存在的 Flink 集群上去，或者被加入到 Flink 应用程序的容器镜像中去。

从 Maven 作业模版(见下文 Maven 作业模版部分)创建的项目，通过 `mvn clean package` 命令会自动把依赖打到应用程序的 jar 包中去。对于没有使用模版进行配置的情况，建议使用 Maven Shade Plugin (配置如附录所示) 来构建包含依赖的 jar 包。

> 对于 Maven（和其他构建工具）来说，要将依赖项正确打包到应用程序 jar 中，这些应用程序依赖项的 scope 必须指定为 `compile`（与核心依赖项不同，核心依赖项的 scope 必须指定为 `provided`）。

## 3. 注意事项

### 3.1 Scala版本

Scala 的不同版本(2.11,2.12等)相互之间是不兼容的。因此，Scala 2.11 对应的 Flink 版本不能用于使用 Scala 2.12 的应用程序。所有依赖(或传递依赖)于 Scala 的 Flink 依赖项都以构建它们的 Scala 版本作为后缀，例如 `flink-streaming-scala_2.11`。只使用 Java 进行开发时可以选择任何 Scala 版本，使用 Scala 开发时需要选择与其应用程序的 Scala 版本匹配的 Flink 依赖版本。

> 2.12.8 之后的 Scala 版本与之前的 2.12.x 版本不兼容，因此 Flink 项目无法将其 2.12.x 版本升级到 2.12.8 之后的版本。用户可以在本地自己编译对应 Scala 版本的 Flink。为了使其能够正常工作，需要添加 -Djapicmp.skip 以在构建时跳过二进制兼容性检查。

### 3.2 Hadoop依赖

一般的规则: 永远不要将 Hadoop 相关依赖直接添加到应用程序中。（唯一的例外是将现有的 Hadoop 输入/输出 Format 与 Flink 的 Hadoop 兼容包一起使用时）如果希望将 Flink 与 Hadoop 结合使用，则需要包含 Hadoop 依赖的 Flink 启动项，而不是将 Hadoop 添加为应用程序依赖项。Flink 将使用 HADOOP_CLASSPATH 环境变量指定的 Hadoop 依赖项，可通过以下方式进行设置：
```
export HADOOP_CLASSPATH**=**hadoop classpath``
```
这种设计有两个主要原因：
- 一些与 Hadoop 的交互可能发生在 Flink 的核心模块中，并且在用户应用程序启动之前，例如为检查点设置 HDFS、通过 Hadoop 的 Kerberos 令牌进行身份验证，或者在 YARN 上进行部署等。
- Flink 的反向类加载机制从核心依赖项中隐藏了许多可传递的依赖项。这不仅适用于 Flink 自己的核心依赖项，而且适用于 Hadoop 的依赖项。这样，应用程序就可以使用相同依赖项的不同版本，而不会发生依赖项冲突（相信我们，这是一件大事，因为 Hadoop 依赖树非常庞大。）

如果在 IDE 内部的测试或开发过程中需要 Hadoop 依赖项（例如 HDFS 访问），请将这些依赖项的 scope 配置为 `test` 或者 `provided`。

## 4. Transform table connector/format resources

Flink 使用 Java 的 Service Provider Interfaces (SPI) 机制通过特定标识符加载 Table 的 connector/format 工厂。由于每个 Table 的 connector/format 的名为 `org.apache.flink.table.factories.Factory` 的 SPI 资源文件位于同一目录：`META-INF/services` 下，因此在构建使用多个 table connector/format 的项目的 uber jar 时，这些资源文件将相互覆盖，这将导致 Flink 无法正确加载工厂类。

在这种情况下，推荐的方法是通过 maven shade 插件的 `ServicesResourceTransformer` 转换 `META-INF/services` 目录下的这些资源文件。给定示例的pom.xml文件内容如下，其中包含连接器 flink-sql-connector-hive-3.1.2 和 flink-parquet format：
```xml
<modelVersion>4.0.0</modelVersion>
<groupId>org.example</groupId>
<artifactId>myProject</artifactId>
<version>1.0-SNAPSHOT</version>

<dependencies>
    <!--  other project dependencies  ...-->
    <dependency>
        <groupId>org.apache.flink</groupId>
        <artifactId>flink-sql-connector-hive-3.1.2__2.11</artifactId>
        <version>1.13.0</version>
    </dependency>

    <dependency>
        <groupId>org.apache.flink</groupId>
        <artifactId>flink-parquet__2.11<</artifactId>
        <version>1.13.0</version>
    </dependency>

</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-shade-plugin</artifactId>
            <executions>
                <execution>
                    <id>shade</id>
                    <phase>package</phase>
                    <goals>
                        <goal>shade</goal>
                    </goals>
                    <configuration>
                        <transformers combine.children="append">
                            <!-- The service transformer is needed to merge META-INF/services files -->
                            <transformer implementation="org.apache.maven.plugins.shade.resource.ServicesResourceTransformer"/>
                            <!-- ... -->
                        </transformers>
                    </configuration>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```
在配置了 ServicesResourceTransformer 之后, 项目构建 uber-ja r时，`META-INF/services` 目录下的这些资源文件会被整合在一起而不是相互覆盖。

## 5. Maven作业模版

强烈建议使用该方式进行配置，可以减少很多重复的配置工作。

### 5.1 前置要求

唯一的环境要求是安装了Maven 3.0.4（或更高版本）和Java 8.x。

### 5.2 创建项目

有两种方式来创建项目。第一种方式使用 Maven archetypes：
```
$ mvn archetype:generate                               \
  -DarchetypeGroupId=org.apache.flink              \
  -DarchetypeArtifactId=flink-quickstart-java      \
  -DarchetypeVersion=1.12.3
```
这允许您命名新创建的项目。它将以交互方式要求您输入 groupId、artifactId 和包名。

第二种方式运行 quickstart 脚本：
```
$ curl https://flink.apache.org/q/quickstart.sh | bash -s 1.12.3
```
我们建议您将此项目导入 IDE 以开发和测试它。IntelliJ IDEA 原生支持 Maven 项目。如果使用 Eclipse，可以使用 m2e 插件导入 Maven 项目。默认情况下，某些 Eclipse 捆绑包包含该插件，否则需要您手动安装。

> 默认的 Java JVM heap size 对于 Flink 来说可能太小了。你必须手动增加它。在 Eclipse 中，选择 `RunConfigurations->Arguments` 并写入VM Arguments 框：`-Xmx800m`。在 IntelliJ IDEA 中，更改 JVM 选项的推荐方法是使用 `Help | Edit Custom VM Options` 选项菜单。

### 5.3 构建项目

如果要生成/打包项目，请转到项目目录并运行 `mvn clean package` 命令。执行后将会得到一个 JAR 文件：`target/-.jar`，其中包含您的应用程序，以及作为依赖项添加到应用程序的连接器和库。

> 如果使用与 StreamingJob 不同的类作为应用程序的主类/入口点，我们建议您相应地更改 pom.xml 文件中的 mainClass 设置。这样，Flink 就可以直接从 JAR 文件运行应用程序，而无需另外指定主类。

## 6. 附录:构建带依赖的 jar 包的模版

要构建包含连接器和库所需的所有依赖项的应用程序 JAR，可以使用以下 shade 插件定义：
```xml
<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-shade-plugin</artifactId>
            <version>3.1.1</version>
            <executions>
                <execution>
                    <phase>package</phase>
                    <goals>
                        <goal>shade</goal>
                    </goals>
                    <configuration>
                        <artifactSet>
                            <excludes>
                                <exclude>com.google.code.findbugs:jsr305</exclude>
                                <exclude>org.slf4j:*</exclude>
                                <exclude>log4j:*</exclude>
                            </excludes>
                        </artifactSet>
                        <filters>
                            <filter>
                                <!-- Do not copy the signatures in the META-INF folder.
                                Otherwise, this might cause SecurityExceptions when using the JAR. -->
                                <artifact>*:*</artifact>
                                <excludes>
                                    <exclude>META-INF/*.SF</exclude>
                                    <exclude>META-INF/*.DSA</exclude>
                                    <exclude>META-INF/*.RSA</exclude>
                                </excludes>
                            </filter>
                        </filters>
                        <transformers>
                            <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                <mainClass>my.programs.main.clazz</mainClass>
                            </transformer>
                        </transformers>
                    </configuration>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

> 原文：[Datastream 开发打包问题](https://developer.aliyun.com/article/859070)
