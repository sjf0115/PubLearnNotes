---
layout: post
author: smartsi
title: ANTLR4 在 IDEA 中使用 ANTLR 与 Java 程序集成
date: 2020-09-12 15:15:01
tags:
  - Antlr

categories: Antlr
permalink: antlr-integrate-with-java
---

> ANTLR4 版本：4.9.2

## 1. 添加依赖

如果想将 ANTLR 自动生成的代码与 Java 程序进行集成，需要在 Maven 项目中添加如下依赖：
```xml
<dependency>
    <groupId>org.antlr</groupId>
    <artifactId>antlr4-runtime</artifactId>
    <version>4.9.2</version>
</dependency>
```

## 2. 下载 ANTLR4 插件

第二件事情就是安装 ANTLR4 插件。在 Plugins 页面搜索 ANTLR4 插件，但是不要着急点击安装，需要判断一下插件对应的 ANTLR4 的版本和我们使用的 ANTLR 版本是否一致：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-1.png?raw=true)

如果一致，直接点击 install 按钮安装即可。否则点击 [Plugin homepage](https://plugins.jetbrains.com/plugin/7358-antlr-v4) 下载对应版本的 ANTLR4 插件：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-2.png?raw=true)

进入主页后在下方找到与你 ANTLR4 版本以及 IDEA 版本相符的插件包下载，在这我们选择的是 1.17 版本([antlr-intellij-plugin-v4-1.17.zip](https://plugins.jetbrains.com/plugin/7358-antlr-v4/versions/stable/144492))，对应 ANTLR4 4.9.2 版本以及 IDEA 2021.3+ 版本：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-3.png?raw=true)

> 下载的插件版本要和 pom 依赖的 ANTLR 版本以及 IDEA 版本相匹配。

然后在 IDEA 中通过磁盘安装插件的方式安装 ANTLR4 插件，安装完重启即可：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-4.png?raw=true)

## 3. 构建和运行 Hello 语法

### 3.1 定义语法文件

在 `src/main` 专门定一个 `antlr4` 目录来定义 `g4` 语法文件。在 `antlr4` 目录下的 `com/antlr/example/hello` 目录下定义 `Hello.g4` 语法文件：
```
grammar Hello; // 定义一个名为 Hello 的语法
r : LITTER ID ; // 定义一个语法规则：匹配一个关键词 hello 和一个紧随其后的标识符
LITTER : 'hello' ;
ID : [a-z]+ ; // 匹配小写字母组成的标识符
WS: [ \t\r\n]+ -> skip; // 忽略空格、Tab、换行以及\r
```
> 为啥在 `com/antlr/example/hello` 目录下定义 `Hello.g4` 语法文件下面会详细介绍。

编辑好 `.g4` 文件后即可测试该语法规则。在语法规则 `r` 处选中 `r` 并右击鼠标后，点击 `Test Rule r`，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-5.png?raw=true)

然后在左下方便可以输入文本信息，在右下方框中便会显示对应的语法分析树：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-6.png?raw=true)

### 3.2 生成程序文件

有两种方法解析 ANTLR4 语法文件 `g4` 并将它们转换为 Java 源文件的方法：
- 手动图形化界面
- 自动 Maven ANTLR4 插件

#### 3.2.1 图形化界面

第一种方式是通过图形化界面手动进行转换。右击项目中刚刚创建的 `Hello.g4` 文件，点击 `Configure ANTLR…`，然后便会弹出如下图所示窗口：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-7.png?raw=true)

需要在 output directory 输入框中配置为 Java 文件输出目录：`/Users/wy/study/code/data-example/antlr-example/src/main/generated-sources/antlr4`，Package 输入框中配置为 Java 文件的包名：`com.antlr.example.hello`。

> 上述配置的 Java 文件为测试目录，最好是放置到 target 下的 generated-sources 目录下

在项目中选中 `Hello.g4` 文件并右击选择 `Generate ANTLR Recognizer`。随后便会在 hello 目录下看到生成的各种 `.java` 文件等：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-8.png?raw=true)

#### 3.2.2 Maven ANTLR4 插件

第二种方式是通过 Maven ANTLR4 插件自动转换。在工程中一般都不会采用在图形化界面中点击按钮来生成 Java 文件(测试时可以采用这种方式)，而 Maven 提供了 `antlr4-maven-plugin` 插件来自动解析 ANTLR4 语法文件(`.g4`)并将它们转换为 Java 源文件。

##### 3.2.2.1 g4 语法文件配置

默认情况下，ANTLR4 会在 `${basedir}/src/main/antlr4` 目录下搜索 `g4` 语法文件，以及在 `${basedir}/src/main/antlr4/imports` 目录下搜索 `.tokens` 文件。如下展示该插件默认配置的预期文件布局：
```
src/main/
      |
      +--- antlr4/...
             |
             +--- imports/
```
antlr4 目录下的语法文件应该存储在子目录中，这些子目录结构与 Java 解析器的包结构对应。如果 Java 解析器的包结构为 `com/antlr/example/hello`，那么语法文件(`*.g4`)应该存储在 `src/main/antlr4/com/antlr/example/hello/Hello.g4`：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-9.png?raw=true)

通过这种方式，生成的 `.java` 文件才能正确地反映包结构：
```java
package com.antlr.example.hello; // 包名
import org.antlr.v4.runtime.atn.*;
...
@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast"})
public class HelloParser extends Parser {
    ...
}
```

##### 3.2.2.2 POM 文件配置

下一步是配置 POM 以调用插件。如果你使用的是默认值，那么下面的代码就足够了：
```xml
<project>
  ...
  <build>
    <plugins>
      <plugin>
        <groupId>org.antlr</groupId>
        <artifactId>antlr4-maven-plugin</artifactId>
        <version>4.3</version>
        <executions>
          <execution>
            <id>antlr</id>
            <goals>
              <goal>antlr4</goal>
            </goals>
          </execution>
        </executions>
      </plugin>
    </plugins>
    ...
  </build>
  ...
</project>
```

但在一些场景下需要单独指定一些参数，而不是默认值，如下是一些常用的参数：
- arguments：要传递给 ANTLR 工具的其他命令行参数列表。例如，通过 `-package` 参数指定生成代码的包名。
- encoding：指定语法文件的编码格式。用户属性为:project.build.sourceEncoding。
- sourceDirectory：ANTLR 语法文件(`*.g4`)所在目录。默认值为 `${basedir}/src/main/antlr4`。
- outputDirectory：指定生成 Java 文件的输出目录。默认值为 `${project.build.directory}/generated-sources/antlr4`。
- treatWarningsAsErrors：将 Warning 视为 Error。默认值为 false。
- visitor：生成语法解析树访问器接口和基类。默认为 false。
- listener：生成语法解析树监听器接口和基类。默认为 true。
- options：显式指定给 ANTLR 工具的语法选项列表。使用 `-D<option>=<value>` 语法将这些选项传递给 ANTLR 工具。

下面插件模板中提供了一些常用的参数：
```xml    
<plugin>
    <groupId>org.antlr</groupId>
    <artifactId>antlr4-maven-plugin</artifactId>
    <executions>
        <execution>
            <id>antlr</id>
            <goals>
                <goal>antlr4</goal>
            </goals>
            <phase>generate-sources</phase>
        </execution>
    </executions>
    <configuration>
        <arguments>
            <!-- 指定生成代码的包名 -->
            <!-- <argument>-package</argument> -->
            <!-- <argument>com.antlr.example</argument> -->
        </arguments>
        <!-- ANTLR 语法文件(*.g4)所在目录 -->
        <sourceDirectory>${basedir}/src/main/antlr4</sourceDirectory>
        <!-- 指定生成 Java 文件的输出目录 -->
        <!-- <outputDirectory>${project.build.directory}/generated-sources/antlr4</outputDirectory>-->
        <!-- Java 文件输出测试目录 -->
        <outputDirectory>${basedir}/src/main/generated-sources/antlr4</outputDirectory>
        <!-- 生成语分析法树监听器代码 -->
        <listener>true</listener>
        <!-- 生成语法分析树访问器代码 -->
        <visitor>true</visitor>
        <!-- 将 Warning 视为 Error -->
        <treatWarningsAsErrors>true</treatWarningsAsErrors>
    </configuration>
</plugin>
```
上述 sourceDirectory 配置将 ANTLR 语法文件(`*.g4`)所在目录设置为 `${basedir}/src/main/antlr4`。outputDirectory 配置将 Java 文件输出目录设置为 `${basedir}/src/main/generated-sources/antlr4`，这是我们的一个测试目录，用于平时开发。如果实际生产中还是建议使用默认值 `${project.build.directory}/generated-sources/antlr4`。使用 visitor 配置生成语法解析树访问器接口和基类。使用 listener 来生成语法解析树监听器接口和基类。

##### 3.2.2.3 Maven 执行

当 mvn 命令执行时，`${basedir}/src/main/antlr4` 下的所有语法文件(除了 src/main/antlr4/imports 下的导入语法外)将被分析并转换为输出目录 `${basedir}/src/main/generated-sources/antlr4` 下的 Java 源码：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-10.png?raw=true)

如果实际生产中还是建议 outputDirectory 使用默认值，输出到 `${project.build.directory}/generated-sources/antlr4` 目录下：

![](https://github.com/sjf0115/ImageBucket/blob/main/Antlr/antlr-integrate-with-java-11.png?raw=true)

### 3.3 执行驱动程序

定义语法文件之后，通过 ANTLR 自动生成代码与 Java 程序进行集成。下面我们使用一个简单的 Java 程序的 main 方法调用我们的语法解析器，并打印和 TestRig 的 `-tree` 选项类似的语法分析树：
```java
public class HelloExpr {
    public static void main(String[] args) throws IOException {
        String input = "hello antlr";
        // 1. 新建一个 CharStream 从字符串中读取数据
        CharStream charStream = CharStreams.fromString(input);
        // 新建一个 CharStream 从标准输入中读取数据
        // CharStream charStream = CharStreams.fromStream(System.in);

        // 2. 创建词法分析器
        HelloLexer lexer = new HelloLexer(charStream);

        // 3. 创建词法符号缓冲区对象
        CommonTokenStream tokens = new CommonTokenStream(lexer);

        // 4. 创建语法分析器
        HelloParser parser = new HelloParser(tokens);

        // 5. 针对 r 语法规则 开始语法分析
        HelloParser.RContext tree = parser.r();

        //5. 打印 语法分析树
        System.out.println(tree.toStringTree(parser));
    }
}
```
语法分析树输出如下：
```
(r hello antlr)
```
> 完整代码: [HelloExpr](https://github.com/sjf0115/data-example/blob/master/antlr-example/src/main/java/com/antlr/example/hello/HelloExpr.java)
