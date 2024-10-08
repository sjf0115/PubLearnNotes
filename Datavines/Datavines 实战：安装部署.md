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

通过你 git 管理工具下载 git 代码：
```
git clone https://github.com/datavane/datavines.git
cd datavines
```

### 2.3 数据库准备

Datavines 的元数据存储在关系型数据库中，目前支持的关系型数据库包括 MySQL 以及 PostgreSQL。下面以 MySQL 为例说明安装步骤：
- 启动数据库并创建新 database 作为 Datavines 元数据库，这里以数据库名 datavines 为例
- 创建完新数据库后，将 script/sql/datavines-mysql.sql 下的 sql 文件直接在 MySQL 中运行，完成数据库初始化

### 2.4 源码编译

如果使用 MySQL 数据库，请注意修改 pom.xml，将 mysql-connector-java 依赖的 scope 改为 compile，使用 PostgreSQL 则不需要：
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>${mysql.version}</version>
   <scope>compile</scope>
</dependency>
```

运行如下命令进行项目构建打包：
```
mvn clean install -Prelease -Dmaven.test.skip=true
```
出现如下界面表示项目已经构建完成：
```
[INFO] datavines-metric-expected-weekly-avg ............... SUCCESS [  1.265 s]
[INFO] datavines-metric-expected-monthly-avg .............. SUCCESS [  1.444 s]
[INFO] datavines-metric-expected-last7day-avg ............. SUCCESS [  1.208 s]
[INFO] datavines-metric-expected-last30day-avg ............ SUCCESS [  1.281 s]
[INFO] datavines-metric-expected-none ..................... SUCCESS [  1.302 s]
[INFO] datavines-metric-expected-all ...................... SUCCESS [  0.070 s]
[INFO] datavines-metric-result-formula-plugins ............ SUCCESS [  0.028 s]
[INFO] datavines-metric-result-formula-count .............. SUCCESS [  1.214 s]
[INFO] datavines-metric-result-formula-diff ............... SUCCESS [  1.178 s]
[INFO] datavines-metric-result-formula-diff-percentage .... SUCCESS [  1.230 s]
[INFO] datavines-metric-result-formula-percentage ......... SUCCESS [  1.292 s]
[INFO] datavines-metric-result-formula-diff-actual-expected SUCCESS [  1.295 s]
[INFO] datavines-metric-result-formula-all ................ SUCCESS [  0.054 s]
[INFO] datavines-core ..................................... SUCCESS [01:35 min]
[INFO] datavines-notification ............................. SUCCESS [  0.039 s]
[INFO] datavines-notification-api ......................... SUCCESS [  1.326 s]
[INFO] datavines-notification-core ........................ SUCCESS [  1.104 s]
[INFO] datavines-notification-plugins ..................... SUCCESS [  0.020 s]
[INFO] datavines-notification-plugin-email ................ SUCCESS [ 18.233 s]
[INFO] datavines-notification-plugin-lark ................. SUCCESS [  1.262 s]
[INFO] datavines-notification-plugin-wecombot ............. SUCCESS [  1.221 s]
[INFO] datavines-notification-plugin-dingtalk ............. SUCCESS [  1.440 s]
[INFO] datavines-registry ................................. SUCCESS [  0.016 s]
[INFO] datavines-registry-api ............................. SUCCESS [  1.079 s]
[INFO] datavines-registry-plugins ......................... SUCCESS [  0.012 s]
[INFO] datavines-registry-mysql ........................... SUCCESS [  1.123 s]
[INFO] datavines-registry-zookeeper ....................... SUCCESS [  2.428 s]
[INFO] datavines-server ................................... SUCCESS [01:28 min]
[INFO] datavines-runner ................................... SUCCESS [ 14.366 s]
[INFO] datavines-dist ..................................... SUCCESS [06:54 min]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  24:56 min
[INFO] Finished at: 2024-09-07T21:56:08+08:00
[INFO] ------------------------------------------------------------------------
```
把打包好的压缩包解压到 `/opt` 工作目录下：
```
localhost:datavines wy$ cd datavines-dist/target
localhost:target wy$ ll
total 968736
drwxr-xr-x  5 wy  staff        160 Sep  7 21:55 ./
drwxr-xr-x  5 wy  staff        160 Sep  7 21:49 ../
drwxr-xr-x  2 wy  staff         64 Sep  7 21:49 archive-tmp/
-rw-r--r--  1 wy  staff  243221743 Sep  7 21:55 datavines-1.0.0-SNAPSHOT-bin.tar.gz
-rw-r--r--  1 wy  staff  243373785 Sep  7 21:56 datavines-1.0.0-SNAPSHOT-bin.zip
localhost:target wy$
localhost:target wy$ tar -zxvf datavines-1.0.0-SNAPSHOT-bin.tar.gz -C /opt
```
创建软连接便于升级：
```
localhost:opt wy$ ln -s datavines-1.0.0-SNAPSHOT-bin/ datavines
```
解压完成以后进入目录
```
localhost:opt wy$ cd datavines
localhost:datavines wy$ ll
total 0
drwxr-xr-x    6 wy    wheel    192 Sep  7 22:52 ./
drwxrwxrwx   71 root  wheel   2272 Sep  7 22:52 ../
drwxr-xr-x    4 wy    wheel    128 Sep  7 22:52 bin/
drwxr-xr-x    7 wy    wheel    224 Sep  7 22:52 conf/
drwxr-xr-x  401 wy    wheel  12832 Sep  7 22:52 libs/
drwxr-xr-x   22 wy    wheel    704 Sep  7 22:52 plugins/
```

### 2.5 配置

编辑配置信息
```
cd conf
vim application.yaml
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
localhost:conf wy$ cd ../bin/
localhost:bin wy$ ll
total 24
drwxr-xr-x  4 wy  wheel   128 Sep  7 22:52 ./
drwxr-xr-x  6 wy  wheel   192 Sep  7 22:52 ../
-rw-r--r--  1 wy  wheel  5062 Sep  7 20:20 datavines-daemon.sh
-rw-r--r--  1 wy  wheel  1506 Sep  7 20:20 datavines-submit.sh
localhost:bin wy$ sh datavines-daemon.sh start mysql
Begin start DataVinesServer mysql......
Starting DataVinesServer, logging to /opt/datavines/bin/../logs/datavines-server-localhost.out ...
nohup /Library/Java/JavaVirtualMachines/jdk1.8.0_161.jdk/Contents/Home/bin/java -Dlogging.config=classpath:server-logback.xml -Dspring.profiles.active=mysql -server -Xmx16g -Xms1g -XX:+UseG1GC -XX:G1HeapRegionSize=8M -classpath /opt/datavines/bin/../conf:/opt/datavines/bin/../libs/* io.datavines.server.DataVinesServer > /opt/datavines/bin/../logs/datavines-server-localhost.out 2>&1 &
End start DataVinesServer mysql.
```
查看日志，如果日志里面没有报错信息，并且能看到 `Started DataVinesServer` 相关日志即证明服务已经成功启动：
```
[INFO] 2024-09-08 17:30:16.630 io.datavines.server.registry.Register:[170] - active server list:[ServerInfo(host=192.168.5.49, serverPort=5600, createTime=2024-09-08 16:54:17.0, updateTime=2024-09-08 17:30:17.0)]
[INFO] 2024-09-08 17:30:16.631 io.datavines.server.registry.Register:[193] - Current slot is 0 total slot is 1
[INFO] 2024-09-08 17:30:16.632 io.datavines.server.dqc.coordinator.runner.JobScheduler:[56] - job scheduler started
[INFO] 2024-09-08 17:30:16.634 io.datavines.server.scheduler.CommonTaskScheduler:[49] - common task scheduler started
[INFO] 2024-09-08 17:30:18.424 org.springframework.boot.autoconfigure.web.servlet.WelcomePageHandlerMapping:[53] - Adding welcome page: class path resource [static/index.html]
[INFO] 2024-09-08 17:30:18.854 org.eclipse.jetty.server.handler.ContextHandler.application:[2347] - Initializing Spring DispatcherServlet 'dispatcherServlet'
[INFO] 2024-09-08 17:30:18.855 org.springframework.web.servlet.DispatcherServlet:[525] - Initializing Servlet 'dispatcherServlet'
[INFO] 2024-09-08 17:30:18.857 org.springframework.web.servlet.DispatcherServlet:[547] - Completed initialization in 2 ms
[INFO] 2024-09-08 17:30:18.890 org.eclipse.jetty.server.AbstractConnector:[331] - Started ServerConnector@39652a30{HTTP/1.1, (http/1.1)}{0.0.0.0:5600}
[INFO] 2024-09-08 17:30:18.891 org.springframework.boot.web.embedded.jetty.JettyWebServer:[172] - Jetty started on port(s) 5600 (http/1.1) with context path '/'
[INFO] 2024-09-08 17:30:20.423 org.springframework.scheduling.quartz.SchedulerFactoryBean:[727] - Starting Quartz Scheduler now
[INFO] 2024-09-08 17:30:20.449 org.springframework.scheduling.quartz.LocalDataSourceJobStore:[3644] - ClusterManager: detected 1 failed or restarted instances.
[INFO] 2024-09-08 17:30:20.450 org.springframework.scheduling.quartz.LocalDataSourceJobStore:[3503] - ClusterManager: Scanning for instance "localhost1725785654454"'s failed in-progress jobs.
[INFO] 2024-09-08 17:30:20.458 org.quartz.core.QuartzScheduler:[547] - Scheduler datavines_$_localhost1725787811975 started.
[INFO] 2024-09-08 17:30:20.474 io.datavines.server.DataVinesServer:[61] - Started DataVinesServer in 19.388 seconds (JVM running for 21.344)
```

## 3. 访问

在浏览器输入：服务器IP:5600 ，就会跳转至登录界面，输入账号密码 admin/123456：

![](img-datavines-setup-1.png)
