## 1. 准备工作

在开始本地运行前，您需要确保您已经安装了 SeaTunnel 所需要的软件：
- 安装Java (Java 8 或 11， 其他高于Java 8的版本理论上也可以工作) 以及设置 JAVA_HOME。

## 2. 下载

进入 SeaTunnel [下载页面](https://seatunnel.apache.org/download)下载最新版本的发布版安装包，目前最新版本为 2.3.5 版本：

SeaTunnel-Web 下载页与 SeaTunnel 在相同的页面，目前最新版本为 1.0.1 版本：

![](img-seatunnel-web-setup-1.png)

## 3. 安装

将下载的压缩包解压缩到指定目录下：
```
tar -zxvf apache-seatunnel-web-1.0.1-bin.tar.gz -C /opt/
```

创建软连接，便于升级：
```
ln -s apache-seatunnel-web-1.0.1-bin/ seatunnel-web
```

## 4. 配置

### 4.1 初始化数据库

初始化数据库有两种方式，一是使用官方提供的初始化脚本，二是直接运行初始化 SQL

#### 4.1.1 使用官方提供的初始化脚本

官方提供了一个 `init_sql.sh` 初始化数据库的脚本，使用之前需要修改 `seatunnel_server_env.sh` 文件来修改环境变量：
```shell
export HOSTNAME="127.0.0.1"
export PORT="3306"
export USERNAME="root"
export PASSWORD="root"
```
> 如果环境变量有冲突需要改下环境变量的名字以及 init_sql.sh 中的环境变量的名字，可以加上前缀 `SEATUNNELT_WEB_` 避免冲突。

修改环境变量之后运行 `init_sql.sh` 来初始化数据库。

### 4.1.2 直接运行初始化 SQL

`init_sql.sh` 初始化数据库的脚本核心是执行 `seatunnel_server_mysql.sql`：
```shell
workDir=`dirname $0`
workDir=`cd ${workDir};pwd`

source ${workDir}/seatunnel_server_env.sh

usage="Usage: seatunnel_server_env.sh must contain hostname/port/username/password."

if [[ ! -n "${HOSTNAME}" ]]  || [[ ! -n "${PORT}" ]] || [[ ! -n "${USERNAME}" ]] || [[ ! -n "${PASSWORD}" ]]; then
    echo $usage
    exit 1
fi

mysql -h${HOSTNAME} -P${PORT} -u${USERNAME} -p${PASSWORD} < ${workDir}/seatunnel_server_mysql.sql
```
所以你也可以直接选择跳过 `init_sql.sh` 初始化数据库的脚本来执行 `seatunnel_server_mysql.sql`。例如，你可以使用 Navicat 导入执行：

![](img-seatunnel-web-setup-2.png)

导入执行完后创建的表如下所示：

![](img-seatunnel-web-setup-3.png)

### 4.2 修改端口与数据源

修改 `conf/application.yml` 配置文件来修改端口号以及 Web 访问数据库的数据源信息：
```yml
server:
  port: 8802

spring:
  application:
    name: seatunnel
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/seatunnel?useSSL=false&useUnicode=true&characterEncoding=utf-8&allowMultiQueries=true&allowPublicKeyRetrieval=true
    username: root
    password: root
  mvc:
    pathmatch:
      matching-strategy: ant_path_matcher
```

### 4.3 配置引擎服务信息

复制引擎服务中配置文件到 Web 配置目录下面。将 hazelcast-client 配置文件拷贝到 Web 的 conf 目录下：
```
cp /opt/seatunnel/config/hazelcast-client.yaml /opt/seatunnel-web/conf/
```
将插件配置文件拷贝到 Web 的 conf 目录下：
```
cp /opt/seatunnel/connectors/plugin-mapping.properties /opt/seatunnel-web/conf/
```

### 4.4 配置 MySQL 驱动

在这我们选择 MySQL 作为元数据库，需要对应的驱动包放到 libs 下：
```
cp mysql-connector-java-8.0.16.jar /opt/seatunnel-web/libs/
```

### 4.5 配置数据源JAR包



## 5. 启动 Web

```
sh bin/seatunnel-cluster.sh
```

配置完成之后可以通过如下命令来启动 Web 服务：
```
sh bin/seatunnel-backend-daemon.sh start
```

![](img-seatunnel-web-setup-4.png)



...
