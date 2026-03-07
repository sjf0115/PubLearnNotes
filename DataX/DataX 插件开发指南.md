本文面向DataX插件开发人员，尝试尽可能全面地阐述开发一个DataX插件所经过的历程，力求消除开发者的困惑，让插件开发变得简单。



从设计之初，DataX 就把异构数据源同步作为自身的使命，为了应对不同数据源的差异、同时提供一致的同步原语和扩展能力，DataX 自然而然地采用了 `框架` + `插件` 的模式：
- 插件只需关心数据的读取或者写入本身。
- 而同步的共性问题，比如：类型转换、性能、统计，则交由框架来处理。

作为插件开发人员，则需要关注两个问题：
- 数据源本身的读写数据正确性。
- 如何与框架沟通、合理正确地使用框架。

下面详细介绍 DataX 的插件机制。

## 1. 插件架构

### 1.1 逻辑执行模型

插件开发者不用关心太多，基本只需要关注特定系统读和写，以及自己的代码在逻辑上是怎样被执行的，哪一个方法是在什么时候被调用的。在此之前，需要明确以下概念：
- `Job`: Job是DataX用以描述从一个源头到一个目的端的同步作业，是DataX数据同步的最小业务单元。比如：从一张mysql的表同步到odps的一个表的特定分区。
- `Task`: Task是为最大化而把Job拆分得到的最小执行单元。比如：读一张有1024个分表的mysql分库分表的Job，拆分成1024个读Task，用若干个并发执行。
- `TaskGroup`: 描述的是一组Task集合。在同一个TaskGroupContainer执行下的Task集合称之为TaskGroup
- `JobContainer`: Job执行器，负责Job全局拆分、调度、前置语句和后置语句等工作的工作单元。类似Yarn中的JobTracker
- `TaskGroupContainer`: TaskGroup执行器，负责执行一组Task的工作单元，类似Yarn中的TaskTracker。

简而言之， Job 拆分成 Task，在分别在框架提供的容器中执行，插件只需要实现 Job 和 Task 两部分逻辑。

### 1.2 物理执行模型

框架为插件提供物理上的执行能力（线程）。DataX 框架有三种运行模式：
- `Standalone`: 单进程运行，没有外部依赖。
- `Local`: 单进程运行，统计信息、错误信息汇报到集中存储。
- `Distrubuted`: 分布式多进程运行，依赖 DataX Service 服务。

当然，上述三种模式对插件的编写而言没有什么区别，你只需要避开一些小错误，插件就能够在单机/分布式之间无缝切换了。当 `JobContainer` 和 `TaskGroupContainer` 运行在同一个进程内时，就是单机模式（Standalone和Local）；当它们分布在不同的进程中执行时，就是分布式（Distributed）模式。

### 1.3 编程接口

那么，`Job` 和 `Task` 的逻辑应怎么对应到具体的代码中的？首先，插件的入口类必须扩展 `Reader` 或 `Writer` 抽象类，并且分别实现 `Job` 和 `Task` 两个内部抽象类，`Job` 和 `Task` 的实现必须是 `内部类` 的形式。以 `Reader` 为例：
```java
public class SomeReader extends Reader {

    public static class Job extends Reader.Job {
        @Override
        public void init() {
        }

    		@Override
    		public void prepare() {
        }

        @Override
        public List<Configuration> split(int adviceNumber) {
            return null;
        }

        @Override
        public void post() {
        }

        @Override
        public void destroy() {
        }
    }

    public static class Task extends Reader.Task {

        @Override
        public void init() {
        }

    		@Override
    		public void prepare() {
        }

        @Override
        public void startRead(RecordSender recordSender) {
        }

        @Override
        public void post() {
        }

        @Override
        public void destroy() {
        }
    }
}
```

Job 接口功能如下：
- `init`: Job 对象初始化工作，此时可以通过 `super.getPluginJobConf()` 获取与本插件相关的配置。读插件获得配置中 reader 部分，写插件获得 writer 部分。
- `prepare`: 全局准备工作，比如odpswriter清空目标表。
- `split`: 拆分Task。参数adviceNumber框架建议的拆分数，一般是运行时所配置的并发度。值返回的是Task的配置列表。
- `post`: 全局的后置工作，比如mysqlwriter同步完影子表后的rename操作。
- `destroy`: Job对象自身的销毁工作。

Task接口功能如下：
- `init`：Task对象的初始化。此时可以通过super.getPluginJobConf()获取与本Task相关的配置。这里的配置是Job的split方法返回的配置列表中的其中一个。
- `prepare`：局部的准备工作。
- `startRead`: 从数据源读数据，写入到 RecordSender 中。RecordSender会把数据写入连接Reader和Writer的缓存队列。
- `startWrite`：从 RecordReceiver 中读取数据，写入目标数据源。RecordReceiver中的数据来自Reader和Writer之间的缓存队列。
- `post`: 局部的后置工作。
- `destroy`: Task象自身的销毁工作。

需要注意的是：
- Job 和 Task 之间一定不能有共享变量，因为分布式运行时不能保证共享变量会被正确初始化。两者之间只能通过配置文件进行依赖。
- prepare 和 post 在 Job 和 Task 中都存在，插件需要根据实际情况确定在什么地方执行操作。

框架按照如下的顺序执行 Job 和 Task 的接口：

![](https://github.com/alibaba/DataX/blob/master/images/plugin_dev_guide_1.png)

上图中，黄色表示 Job 部分的执行阶段，蓝色表示 Task 部分的执行阶段，绿色表示框架执行阶段。

![](https://github.com/alibaba/DataX/blob/master/images/plugin_dev_guide_2.png)

## 2. 插件开发

### 2.1 Maven POM 文件配置

#### 2.1.1 插件依赖

pom.xml 添加如下关键依赖：
```xml
<!-- DataX -->
<dependency>
    <groupId>com.alibaba.datax</groupId>
    <artifactId>datax-common</artifactId>
    <version>${datax-project-version}</version>
    <exclusions>
        <exclusion>
            <artifactId>slf4j-log4j12</artifactId>
            <groupId>org.slf4j</groupId>
        </exclusion>
    </exclusions>
</dependency>
```

#### 2.1.2 Maven 插件配置

核心需要引入 `Maven-assembly-plugin` 插件，目的是要将写的程序和它本身所依赖的 jar 包一起 build 到一个包里，是 Maven 中针对打包任务而提供的标准插件：
```xml
<build>
    <plugins>
        <!-- compiler plugin -->
        <plugin>
            <artifactId>maven-compiler-plugin</artifactId>
            <configuration>
                <source>${jdk-version}</source>
                <target>${jdk-version}</target>
                <encoding>${project-sourceEncoding}</encoding>
            </configuration>
        </plugin>
        <!-- assembly plugin -->
        <plugin>
            <artifactId>maven-assembly-plugin</artifactId>
            <configuration>
                <descriptors> <!--描述文件路径-->
                    <descriptor>src/main/assembly/package.xml</descriptor>
                </descriptors>
                <finalName>datax</finalName>
            </configuration>
            <executions>
                <execution>
                    <id>dwzip</id>
                    <phase>package</phase> <!-- 绑定到package生命周期阶段上 -->
                    <goals>
                        <goal>single</goal> <!-- 只运行一次 -->
                    </goals>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

### 2.2 配置 package.xml 文件

在上述 assembly plugin 插件的 descriptor 中定义了描述文件路径 `src/main/assembly/package.xml`，那么就需要在 `src/main/assembly/` 路径下创建 `package.xml` 描述文件：
```xml
<assembly
        xmlns="http://maven.apache.org/plugins/maven-assembly-plugin/assembly/1.1.0"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/plugins/maven-assembly-plugin/assembly/1.1.0 http://maven.apache.org/xsd/assembly-1.1.0.xsd">
    <id></id>
    <formats>
        <format>dir</format>
    </formats>
    <includeBaseDirectory>false</includeBaseDirectory>
    <fileSets>
        <fileSet>
            <directory>src/main/resources</directory>
            <includes>
                <include>plugin.json</include>
            </includes>
            <outputDirectory>plugin/writer/demowriter</outputDirectory>
        </fileSet>
        <fileSet>
            <directory>target/</directory>
            <includes>
                <include>demowriter-0.0.1-SNAPSHOT.jar</include>
            </includes>
            <outputDirectory>plugin/writer/demowriter</outputDirectory>
        </fileSet>
    </fileSets>

    <dependencySets>
        <dependencySet>
            <useProjectArtifact>false</useProjectArtifact>
            <outputDirectory>plugin/writer/demowriter/libs</outputDirectory>
            <scope>runtime</scope>
        </dependencySet>
    </dependencySets>
</assembly>
```

### 2.3 配置插件描述文件

代码写好了，有没有想过框架是怎么找到插件的入口类的？框架是如何加载插件的呢？在每个插件的项目中，都有一个 `plugin.json` 插件描述文件，这个文件定义了插件的相关信息，包括入口类。在 `src/main/resources/` 下创建 `plugin.json` 文件：
```json
{
  "name": "demowriter",
  "class": "com.alibaba.datax.plugin.writer.demowriter.DemoWriter",
  "description": "Demo Writer",
  "developer": "sjf0115"
}
```
- name: 插件名称，大小写敏感。框架根据用户在配置文件中指定的名称来搜寻插件。十分重要 。
- class: 入口类的全限定名称，框架通过反射插件入口类的实例。十分重要 。
- description: 描述信息。
- developer: 开发人员。

### 2.4 代码开发

要实现 DemoWriter，首先插件的入口类必须扩展 Writer 抽象类，并且分别实现 Job 和 Task 两个内部抽象类：
```java
public class DemoWriter extends Writer {
    public static class Job extends Writer.Job {
        @Override
        public void init() {

        }

        @Override
        public List<Configuration> split(int mandatoryNumber) {
            return Collections.emptyList();
        }

        @Override
        public void destroy() {

        }

        ...
    }

    public static class Task extends Writer.Task {
        @Override
        public void init() {

        }

        @Override
        public void startWrite(RecordReceiver lineReceiver) {

        }

        @Override
        public void destroy() {

        }

        ...
    }
}
```
> Job 和 Task 的实现必须是内部类的形式。

## 3. 插件发布

DataX 使用 assembly 打包。打包命令如下：
```
mvn -U clean package assembly:assembly -Dmaven.test.skip=true -pl :demowriter -am -Dautoconfig.skip
```
DataX 插件需要遵循统一的目录结构：
```
${DATAX_HOME}
├── bin
│   ├── datax.py
│   ├── dxprof.py
│   └── perftrace.py
├── conf
│   ├── core.json
│   └── logback.xml
├── job
│   └── job.json
├── lib
│   ├── datax-core-0.0.1-SNAPSHOT.jar
├── plugin
│   ├── reader
│   │   ├── clickhousereader
│   │   │   ├── clickhousereader-0.0.1-SNAPSHOT.jar
│   │   │   ├── libs
│   |   │   │   ├── clickhouse-jdbc-0.2.4.jar
│   │   │   │   ├── datax-core-0.0.1-SNAPSHOT.jar
│   │   │   ├── plugin.json
│   │   │   └── plugin_job_template.json
│   └── writer
│       ├── clickhousewriter
│       │   ├── clickhousewriter-0.0.1-SNAPSHOT.jar
│       │   ├── libs
│       │   │   ├── clickhouse-jdbc-0.2.4.jar
│       │   │   ├── datax-core-0.0.1-SNAPSHOT.jar
│       │   ├── plugin.json
│       │   └── plugin_job_template.json
├── script
│   └── Readme.md
└── tmp
    └── readme.txt
```
插件目录规范如下：
- `${DATAX_HOME}/bin`: 可执行程序目录。
- `${DATAX_HOME}/conf`: 框架配置目录。
- `${DATAX_HOME}/lib`: 框架依赖库目录。
- `${DATAX_HOME}/plugin`: 插件目录。

插件目录分为 reader 和 writer 子目录，分别存放读写插件。插件 reader 和 writer 子目录规范如下：
- `${DATAX_HOME}/plugin/libs`: 插件的依赖库。
- `${DATAX_HOME}/plugin/plugin-name-version.jar`: 插件本身的 jar。
- `${DATAX_HOME}/plugin/plugin.json`: 插件描述文件。

需要注意的是插件的目录名字必须和 `plugin.json` 中定义的插件名称一致。

## 4. 插件使用

DataX 使用 json 作为配置文件的格式。一个典型的 DataX 任务配置如下：
```
{
  "job": {
    "content": [
      {
        "reader": {
          "name": "odpsreader",
          "parameter": {
            "accessKey": "",
            "accessId": "",
            "column": [""],
            "isCompress": "",
            "odpsServer": "",
            "partition": [
              ""
            ],
            "project": "",
            "table": "",
            "tunnelServer": ""
          }
        },
        "writer": {
          "name": "oraclewriter",
          "parameter": {
            "username": "",
            "password": "",
            "column": ["*"],
            "connection": [
              {
                "jdbcUrl": "",
                "table": [
                  ""
                ]
              }
            ]
          }
        }
      }
    ]
  }
}
```
DataX 框架有 core.json 配置文件，指定了框架的默认行为。任务的配置里头可以指定框架中已经存在的配置项，而且具有更高的优先级，会覆盖 core.json 中的默认值。

配置中 `job.content.reader.parameter` 的 value 部分会传给 Reader.Job；`job.content.writer.parameter` 的 value 部分会传给 Writer.Job ，Reader.Job 和 Writer.Job 可以通过 `super.getPluginJobConf()` 来获取。

DataX框架支持对特定的配置项进行RSA加密，例子中以*开头的项目便是加密后的值。 配置项加密解密过程对插件是透明，插件仍然以不带*的key来查询配置和操作配置项 。
