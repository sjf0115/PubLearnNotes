## 1. 平台介绍

Datavines 是一站式开源数据可观测性平台，提供元数据管理、数据概览报告、数据质量管理，数据分布查询、数据趋势洞察等核心能力，致力于帮助用户全面地了解和掌管数据，让您做到心中有数.

## 2. 快速部署

### 2.1 环境准备

在安装 Datavines 之前请确保你的服务器上已经安装下面软件：
- Git，确保 git clone 的顺利执行
- JDK，确保 jdk >= 8
- Maven, 确保 maven >= 3.6.0
- MySQL, 确保版本 >=5.7

需要注意的是 Maven 需要至少 3.6.0 版本，否则在编译时会出现如下异常：
```java
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 48.752 s
[INFO] Finished at: 2024-09-07T20:44:30+08:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal com.github.eirslett:frontend-maven-plugin:1.12.1:install-node-and-npm (install node and npm) on project datavines-ui: The plugin com.github.eirslett:frontend-maven-plugin:1.12.1 requires Maven version 3.6.0 -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/PluginIncompatibleException
[ERROR]
[ERROR] After correcting the problems, you can resume the build with the command
[ERROR]   mvn <goals> -rf :datavines-ui
```

### 2.2 下载代码

```
git clone https://github.com/datavane/datavines.git
cd datavines
```

### 2.3 数据库准备

Datavines 的元数据是存储在关系型数据库中，目前支持 MySQL ，下面以 MySQL 为例说明安装步骤：
- 创建数据库 datavines
- 执行 script/sql/datavines-mysql.sql 脚本进行数据库的初始化

### 2.4 项目构建

打包并解压
```
mvn clean package -Prelease
cd datavines-dist/target
tar -zxvf datavines-1.0.0-SNAPSHOT-bin.tar.gz
```
解压完成以后进入目录
```
cd datavines-1.0.0-SNAPSHOT-bin
```
### 2.5 配置

编辑配置信息
```
cd conf
vi application.yaml
```
修改数据库信息：
```
spring:
 datasource:
   driver-class-name: com.mysql.cj.jdbc.Driver
   url: jdbc:mysql://127.0.0.1:3306/datavines?useUnicode=true&characterEncoding=UTF-8
   username: root
   password: 123456
```
如果你是使用 Spark 做为执行引擎，并且是提交到 yarn 上面去执行的，那么需要在 common.properties 中配置 yarn 相关的信息:
```
# standalone 模式
yarn.mode=standalone
yarn.application.status.address=http://%s:%s/ws/v1/cluster/apps/%s #第一个%s需要被替换成yarn的ip地址
yarn.resource.manager.http.address.port=8088

# ha 模式
yarn.mode=ha
yarn.application.status.address=http://%s:%s/ws/v1/cluster/apps/%s
yarn.resource.manager.http.address.port=8088
yarn.resource.manager.ha.ids=192.168.0.1,192.168.0.2
```

### 2.6 启动服务
```
cd bin
sh datavines-daemon.sh start mysql
```
查看日志，如果日志里面没有报错信息，并且能看到[INFO] 2022-04-10 12:29:05.447 io.datavines.server.DatavinesServer:[61] - Started DatavinesServer in 3.97 seconds (JVM running for 4.69) 的时候，证明服务已经成功启动。

## 3. 访问

在浏览器输入：服务器IP:5600 ，就会跳转至登录界面，输入账号密码 admin/123456：
```

```




。。。
