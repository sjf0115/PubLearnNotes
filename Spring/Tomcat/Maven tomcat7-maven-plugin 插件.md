以前我们在开发 Java Web 项目时（一般都是 Tomcat Web 应用服务器），[安装使用本地的 Tomcat](https://blog.csdn.net/SunnyYoona/article/details/131368113)，并配置发布环境。但在实际地开发过程中，使用独立的 Tomcat 服务器，往往会比较浪费时间。如果你使用 Maven 开发 Java Web 项目时，你可以选择使用 Tomcat 插件(`tomcat7-maven-plugin`)来代替安装本地 Tomcat。这样做有以下好处：
- 配置简单(相对配置 Tomcat 服务器环境而言)；
- 每次都是新发布，确保后端的修改能及时在应用中体现
- 远程热部署能力强(克服tomcat热部署弱的缺陷)

## 1. 引入

```xml
<build>
    <plugins>
        <!-- Tomcat7 插件-->
        <plugin>
            <groupId>org.apache.tomcat.maven</groupId>
            <artifactId>tomcat7-maven-plugin</artifactId>
            <version>2.2</version>
            <configuration>
                <port>8070</port>
                <path>/</path>
                <uriEncoding>UTF-8</uriEncoding>
                <server>tomcat7</server>
            </configuration>
        </plugin>
    </plugins>
</build>
```
tomcat7-maven-plugin 是很久以前的插件版本，默认支持到 Tomcat7，但是对于目前最新的 Tomcat9 同样可以使用该插件。


## 2. 支持的目标

默认使用的 Tomcat7 插件支持多种目标，调用格式如下：
```
mvn tomcat7:[goal]
```
例如，远程部署一个项目到Tomcat容器：
```
mvn tomcat7:deploy
```

| 目标 | 说明  |
| :------------- | :------------- |
| deploy  | 部署 Web war 包到 Tomcat 中  |
| deploy-only | 不经过package阶段，直接将包部署到Tomcat中 |
| redeploy  | 重新部署 Web war 包到 Tomcat 中  |
| undeploy  | 停止该项目运行并从 Tomcat 服务器中取消部署的项目  |
| run  | 将当前项目作为动态web程序(exploded)，使用嵌入的Tomcat服务器运行  |

## 3. 运行

使用 Maven 运行 Tomcat




但是如果想要调试，就必须使用编辑器的maven插件。比如在idea中，我们直接在Run/Debug Configuration->Maven->Commandline中输入 clean tomcat7:run 即可。

上述方式调试，页面修改可以直接显示，后台代码可以使用Jrebel热部署。
