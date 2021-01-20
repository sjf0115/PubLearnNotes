
## 1. 编译

```
sudo tar -zxvf apache-ranger-2.1.0.tar.gz -C /opt/
```

> 需要检查是否已经安装了 Git、Maven 以及 Python2，注意不能安装 Python3

```
mvn clean compile package assembly:assembly install -DskipTests=true -Drat.skip=true -Dmaven.test.skip=true
```
由于编译时间比较长，可以放后台执行：
```
nohup mvn clean compile package assembly:assembly install -DskipTests=true -Drat.skip=true -Dmaven.test.skip=true > maven.log &
```
编译完成后，在当前 target 目下会生成对应的 tar 文件，如下所示：

![]()

## 2. 安装

### 2.1 安装MySQL

具体如何安装 MySQL 自行百度，在这默认已经安装成功。

```
create database ranger;
grant all on *.* to 'root'@'%' identified by 'root';
Flush privileges;
```

### 2.2 安装Solr

具体参考[Solr 安装与部署](http://smartsi.club/how-install-and-startup-solr.html)

### 2.3 安装Ranger

进入 target 目录，解压 ranger-1.2.0-admin.tar.gz 包：
```
cd /opt/apache-ranger-1.2.0/target/
tar -zxvf ranger-1.2.0-admin.tar.gz -C /opt
```

修改配置文件 install.properties：

安全策略存储：
```
DB_FLAVOR=MYSQL
#SQL_CONNECTOR_JAR=/opt/ranger-1.2.0-admin/lib/mysql-connector-java-8.0.17.jar
db_root_user=root
db_root_password=root
db_host=localhost

db_name=ranger
db_user=root
db_password=root
```
审计日志存储
```
audit_store=solr
audit_solr_urls=http://localhost:8983/solr/ranger_audits
audit_solr_user=
audit_solr_password=
audit_solr_zookeepers=
```
> 如果没有安装 Solr 置空即可。

Ranger
```
rangerAdmin_password=ranger_root
rangerTagsync_password=ranger_root
rangerUsersync_password=ranger_root
keyadmin_password=ranger_root
```
策略管理配置：
```
policymgr_external_url=http:localhost:6080
```
启动 Ranger admin 进程的 Linux 用户信息：
```
unix_user=ranger
unix_user_pwd=ranger
unix_group=ranger
```
Hadoop 的配置文件目录：
```
hadoop_conf=/opt/hadoop/etc/hadoop
```


需要使用root用户执行脚本：

```
./setup.sh: line 1194: groupadd: command not found
2021-01-17 21:30:06,3N  [E] Creating group ranger failed
```





...
