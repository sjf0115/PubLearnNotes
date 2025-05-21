## 1.准备

为了顺利成功安装 StreamPark，首先需要准备好如下的环境：

| 环境 | 版本要求 | 是否必须 | 备注 |
| :------------- | :------------- |
| 操作系统  | Linux/MacOS | 是 | 不支持 Windows 系统 |
| Java	| 1.8+	|	是 | Java version >=1.8 |
| Scala	2.12+	| 是 |	Scala version >=2.12 |
| 数据库	| MySQL: 5.6+、Postgresql: 9.6+	| 否 |	默认使用 H2 数据库，支持 MySQL 和 Postgresql |
| Flink	| 1.12+	| 否 |	Flink 版本最低支持1.12 |
| Hadoop |	2+	|	否 | 非必须，如果部署作业至 Yarn，需要准备 Hadoop 环境 |
| Kubernetes |	1.16+	| 否 |	非必须，如果部署作业至 Kubernetes，需要准备 Kubernetes 集群 |

## 2.下载

您可以直接从官网下载最新版的 StreamPark，本文使用的是 2.1.5 版本，下载地址：https://streampark.apache.org/download

下载完成后，解压：
```
# 解压 streampark 安装包.
tar -zxvf apache-streampark_2.12-2.1.5-incubating-bin.tar.gz
```

可以看到解压后的目录如下：
```
├── bin
│    ├── startup.sh 							                        //启动脚本
│    ├── shutdown.sh 						                            //停止脚本
│    └── ......
├── conf
│    ├── config.yaml 						                            //项目配置文件
│    └── logback-spring.xml 				                            //日志配置文件
├── lib
│    └── *.jar 								                            //项目的 jar 包
├── logs 									                            //程序 log 目录
├── script
│    ├── data
│    │   ├── mysql-data.sql 					                        // mysql的ddl建表sql
│    │   └── pgsql-data.sql 					                        // pgsql的ddl建表sql
│    ├── schema
│    │   ├── mysql-schema.sql 				                            // mysql的完整初始化数据
│    │  └── pgsql-schema.sql 				                            // pgsql的完整初始化数据
│    └── upgrade
│        ├── mysql
│        │   ├── 1.2.3.sql 					                            //升级到 1.2.3版本需要执行的升级sql    
│        │   ├── 2.0.0.sql 					                            //升级到 2.0.0版本需要执行的升级sql
│        │   ├── ......
│        └── pgsql
│            └── ......  
└── temp 									                            //内部使用到的临时路径，不要删除
```
## 3. 配置

### 3.1 使用外部数据库

默认是使用 H2 本地数据库来启动程序的，如果想集成外部 MySQL 或 Postgresql 数据库，需要修改安装目录下的 conf/config.yaml 文件，核心修改内容如下（这里以 MySQL 为例子）：
```
datasource:
  dialect: mysql
  username:  root
  password:  root
  url: jdbc:mysql://localhost:3306/streampark?useUnicode=true&characterEncoding=UTF-8&useJDBCCompliantTimezoneShift=true&useLegacyDatetimeCode=false&serverTimezone=GMT%2B8
```
接着需要手动连接外部数据库，并初始化 MySQL 建表脚本（位置：安装目录 /script/schema/mysql-schema.sql ）以及数据初始化脚本（位置：安装目录/script/data/mysql-data.sql）

以上步骤都准备好了，启动服务即可自动连接并使用外部的数据库。

### 3.2 使用 Hadoop

如果需要部署作业至 YARN，则需要配置 Hadoop 相关的环境变量。假如您是基于 CDH 安装的 hadoop 环境， 相关环境变量可以参考如下配置:
```
export HADOOP_HOME=/opt/cloudera/parcels/CDH/lib/hadoop #hadoop 安装目录
export HADOOP_CONF_DIR=/etc/hadoop/conf
export HIVE_HOME=$HADOOP_HOME/../hive
export HADOOP_HDFS_HOME=$HADOOP_HOME/../hadoop-hdfs
export HADOOP_MAPRED_HOME=$HADOOP_HOME/../hadoop-mapreduce
export HADOOP_YARN_HOME=$HADOOP_HOME/../hadoop-yarn
```
> StreamPark 服务会自动从上述配置的环境变量里读取 hadoop 路径下的配置，连接 hadoop，上传资源至 hdfs 以及部署作业至 yarn。

### 3.3 配置文件

除此，安装目录下的 conf/config.yaml 文件可能需要修改（例如指定 hadoop 用户、kerberos 认证等），核心修改内容如下：
```
streampark:
  workspace:
    # 存储资源至 hdfs 的根路径
    remote: hdfs:///streampark/
  proxy:
    # hadoop yarn 代理路径, 例如: knox 进程地址 https://streampark.com:8443/proxy/yarn
    yarn-url:
  yarn:
    # 验证类型
    http-auth: 'simple'  # 默认 simple或 kerberos
  # flink on yarn or spark on yarn, HADOOP_USER_NAME
  hadoop-user-name: hdfs
```

### 3.4 其它配置

最后附上 config.yaml 的配置详解，可以让您轻松地进一步集成 SSO 或 LDAP 等。

```xml
########################################### 日志相关配置 ###########################################
logging:
  level:
    root: info  

########################################### 服务基础配置 ###########################################
server:
  port: 10000  
  session:
    ttl: 2h  # 用户登录会话的有效期。如果会话超过这个时间，用户会被自动注销。
  undertow:  # Undertow 服务设置
    buffer-size: 1024  
    direct-buffers: true  
    threads:
      io: 16  
      worker: 256  

########################################### 数据库相关配置 ###########################################
datasource:
  dialect: h2  # 数据库方言，支持 h2、mysql、pgsql
  h2-data-dir: ~/streampark/h2-data  # 如果使用 h2 数据库，则需要配置数据目录
  username:  
  password:  
  url:  # 数据库连接URL，示例: jdbc:mysql://localhost:3306/streampark?......

########################################### 项目基础配置 ###########################################
streampark:
  ## 工作区配置，分为本地和 hdfs 工作区，用于相关不同类型的资源
  workspace:
    local: /tmp/streampark  
    remote: hdfs:///streampark/
  ## 代理相关
  proxy:
    lark-url:  # 飞书代理地址
    yarn-url:  # Yarn 的代理路径
  ## yarn相关
  yarn:
    http-auth: 'simple'  # 认证方式
  hadoop-user-name: hdfs  # 配置 Hadoop 用户名
  ## 项目管理相关
  project:
    max-build: 16  # 同时运行的最大项目数量。
  ## 开发接口相关
  openapi:
    white-list:  # 配置开放 API 的白名单

########################################### kerberos 认证配置 ###########################################
security:
  kerberos:
    login:
      debug: false  
      enable: false  
      keytab:
      krb5:  
      principal:  
    ttl: 2h  

########################################### ldap 认证配置 ###########################################
ldap:
  base-dn: dc=streampark,dc=com  
  enable: false  
  username: cn=Manager,dc=streampark,dc=com  
  password: streampark  
  urls: ldap://99.99.99.99:389  
  user:
    email-attribute: mail  
    identity-attribute: uid
```


## 4. 启动

进入安装目录下的 bin 目录，启动：
```
# 进入安装目录下的 bin 目录
cd bin
# 启动程序
./startup.sh
```
> 启动程序后，可能会报如下错误：streampark.workspace.local: "/tmp/streampark" is an invalid path, please reconfigure in xxx/conf/config.yaml

这是因为 streampark 的本地工作目录不存在或者是没有指定合法的目录，处理方式很简单，可以直接使用默认配置，在 /tmp 目录直接新建 streampark 目录:
```
mkdir -p /tmp/streampark
```
或者配置安装路径下的 conf/config.yaml 文件的 streampark.workspace.local 的属性值为一个合法的本地路径。再次执行 startup.sh，可以看到程序启动成功：

![]()

访问 StreamPark，地址：http://127.0.0.1:10000

> 账号密码: admin / streampark









....
