---
layout: post
author: sjf0115
title: ElasticSearch安装与启动
date: 2016-06-23 23:15:17
tags:
  - ElasticSearch

categories: ElasticSearch
permalink: elasticsearch-setup-and-run
---

### 1. 检查JDK版本

使用如下命令检验JDK版本：
```
xiaosi@Qunar:~$ java -version
java version "1.7.0_40"
Java(TM) SE Runtime Environment (build 1.7.0_40-b43)
Java HotSpot(TM) 64-Bit Server VM (build 24.0-b56, mixed mode)
xiaosi@Qunar:~$
```
如果你的JDK版本为1.7，有可能会遇到如下问题：
```
xiaosi@Qunar:~/opt/elasticsearch-2.3.3/bin$ ./elasticsearch
Exception in thread "main" java.lang.RuntimeException: Java version: Oracle Corporation 1.7.0_40 [Java HotSpot(TM) 64-Bit Server VM 24.0-b56] suffers from critical bug https://bugs.openjdk.java.net/browse/JDK-8024830 which can cause data corruption.
Please upgrade the JVM, see http://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html for current recommendations.
If you absolutely cannot upgrade, please add -XX:-UseSuperWord to the JAVA_OPTS environment variable.
Upgrading is preferred, this workaround will result in degraded performance.
	at org.elasticsearch.bootstrap.JVMCheck.check(JVMCheck.java:123)
	at org.elasticsearch.bootstrap.Bootstrap.init(Bootstrap.java:268)
	at org.elasticsearch.bootstrap.Elasticsearch.main(Elasticsearch.java:35)
Refer to the log for complete error details.
```
主要原因是Elasticsearch至少需要Java 8.


### 2. 安装ElasticSearch

#### 2.1 下载
检查JDK版本之后，我们可以下载并运行Elasticsearch。 二进制文件可以从　www.elastic.co/downloads　获取，过去版本也可以从中获取。 对于每个版本，您可以选择zip或tar存档，或DEB或RPM软件包。 为了简单起见，我们使用tar文件。

我们下载Elasticsearch 2.3.3 为例：
```
xiaosi@Qunar:~$ curl -L -O https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.3.3/elasticsearch-2.3.3.tar.gz
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 26.2M  100 26.2M    0     0   190k      0  0:02:21  0:02:21 --:--:--  211k
```

具体的下载版本可以查看：https://www.elastic.co/downloads/elasticsearch

#### 2.2 解压
```
xiaosi@Qunar:~$ tar -zxvf elasticsearch-2.3.3.tar.gz -C /home/xiaosi/opt
elasticsearch-2.3.3/README.textile
elasticsearch-2.3.3/LICENSE.txt
elasticsearch-2.3.3/NOTICE.txt
elasticsearch-2.3.3/modules/
elasticsearch-2.3.3/modules/lang-groovy/
elasticsearch-2.3.3/modules/reindex/
elasticsearch-2.3.3/modules/lang-expression/
elasticsearch-2.3.3/modules/lang-groovy/plugin-security.policy
```
解压完之后如下：
```
xiaosi@Qunar:~/opt$ cd elasticsearch-2.3.3/
xiaosi@Qunar:~/opt/elasticsearch-2.3.3$ ls
bin  config  lib  LICENSE.txt  modules  NOTICE.txt  README.textile
```
#### 2.3 启动

##### 2.3.1 启动帮助
```
xiaosi@Qunar:~/opt/elasticsearch-2.3.3/bin$ ./elasticsearch -help
NAME
    start - Start Elasticsearch
SYNOPSIS
    elasticsearch start
DESCRIPTION
    This command starts Elasticsearch. You can configure it to run in the foreground, write a pid file
    and configure arbitrary options that override file-based configuration.
OPTIONS
    -h,--help                    Shows this message
    -p,--pidfile <pidfile>       Creates a pid file in the specified path on start
    -d,--daemonize               Starts Elasticsearch in the background
    -Dproperty=value             Configures an Elasticsearch specific property, like -Dnetwork.host=127.0.0.1
    --property=value             Configures an elasticsearch specific property, like --network.host 127.0.0.1
    --property value
    NOTE: The -d, -p, and -D arguments must appear before any --property arguments.
xiaosi@Qunar:~/opt/elasticsearch-2.3.3/bin$
```
##### 2.3.2 启动
```
xiaosi@Qunar:~/opt/elasticsearch-2.3.3/bin$ ./elasticsearch
[2016-06-23 22:06:36,034][INFO ][node                     ] [Venom] version[2.3.3], pid[21245], build[218bdf1/2016-05-17T15:40:04Z]
[2016-06-23 22:06:36,035][INFO ][node                     ] [Venom] initializing ...
[2016-06-23 22:06:36,475][INFO ][plugins                  ] [Venom] modules [reindex, lang-expression, lang-groovy], plugins [], sites []
[2016-06-23 22:06:36,493][INFO ][env                      ] [Venom] using [1] data paths, mounts [[/ (/dev/sda7)]], net usable_space [9.6gb], net total_space [41.5gb], spins? [no], types [ext4]
[2016-06-23 22:06:36,493][INFO ][env                      ] [Venom] heap size [990.7mb], compressed ordinary object pointers [true]
[2016-06-23 22:06:38,041][INFO ][node                     ] [Venom] initialized
[2016-06-23 22:06:38,041][INFO ][node                     ] [Venom] starting ...
[2016-06-23 22:06:38,097][INFO ][transport                ] [Venom] publish_address {127.0.0.1:9300}, bound_addresses {[::1]:9300}, {127.0.0.1:9300}
[2016-06-23 22:06:38,102][INFO ][discovery                ] [Venom] elasticsearch/CCQnbPSBQQmVK3c8f4CbHg
[2016-06-23 22:06:41,167][INFO ][cluster.service          ] [Venom] new_master {Venom}{CCQnbPSBQQmVK3c8f4CbHg}{127.0.0.1}{127.0.0.1:9300}, reason: zen-disco-join(elected_as_master, [0] joins received)
[2016-06-23 22:06:41,190][INFO ][http                     ] [Venom] publish_address {127.0.0.1:9200}, bound_addresses {[::1]:9200}, {127.0.0.1:9200}
[2016-06-23 22:06:41,190][INFO ][node                     ] [Venom] started
[2016-06-23 22:06:41,232][INFO ][gateway                  ] [Venom] recovered [0] indices into cluster_state
```
##### 2.3.3 验证

在浏览器中输入：http://localhost:9200/   （elasticsearch默认端口号为9200）
```
{
name: "Ulysses",
cluster_name: "elasticsearch",
version: {
number: "2.3.3",
build_hash: "218bdf10790eef486ff2c41a3df5cfa32dadcfde",
build_timestamp: "2016-05-17T15:40:04Z",
build_snapshot: false,
lucene_version: "5.5.0"
},
tagline: "You Know, for Search"
}
```
health状况：
```
xiaosi@Qunar:~$ curl 'localhost:9200/_cat/health?v'
epoch      timestamp cluster       status node.total node.data shards pri relo init unassign pending_tasks max_task_wait_time active_shards_percent
1466691011 22:10:11  elasticsearch green           1         1      0   0    0    0        0             0                  -                100.0%
xiaosi@Qunar:~$
```
备注：（status）
```
绿色表示一切是好的(集群功能齐全)
黄色意味着所有数据是可用的，但是一些副本尚未分配(集群功能齐全)
红色意味着一些数据不可用
即使一个集群是红色的,它仍然是部分功能(即它将继续搜索请求从服务可用的碎片)但是你可能需要尽快修复它,因为你有缺失的数据。
```

##### 2.3.5 说明

刚开始安装在/opt目录下，普通用户是没有权限的，在启动elasticsearch时会告诉你权限不够：
```
xiaosi@Qunar:~$ cd /opt/elasticsearch-2.3.3/
xiaosi@Qunar:/opt/elasticsearch-2.3.3$ cd bin/
xiaosi@Qunar:/opt/elasticsearch-2.3.3/bin$ ./elasticsearch
log4j:ERROR setFile(null,true) call failed.
java.io.FileNotFoundException: /opt/elasticsearch-2.3.3/logs/elasticsearch.log (权限不够)
	at java.io.FileOutputStream.open0(Native Method)
	at java.io.FileOutputStream.open(FileOutputStream.java:270)
```
权限不够，那就用root用户去启动elasticsearch，会告诉你不能使用root用户来启动elasticsearch：
```
xiaosi@Qunar:/opt/elasticsearch-2.3.3/bin$ sudo ./elasticsearch
Exception in thread "main" java.lang.RuntimeException: don't run elasticsearch as root.
	at org.elasticsearch.bootstrap.Bootstrap.initializeNatives(Bootstrap.java:93)
	at org.elasticsearch.bootstrap.Bootstrap.setup(Bootstrap.java:144)
	at org.elasticsearch.bootstrap.Bootstrap.init(Bootstrap.java:270)
	at org.elasticsearch.bootstrap.
```
所以只好安装在自己的目录下。对此不知道有什么解决之道？

### 3. 安装Kibana

#### 3.1 下载地址
```
https://www.elastic.co/downloads/kibana
```

![](http://img.blog.csdn.net/20160623230109514)

备注：
```
Kibana 4.5.x requires Elasticsearch 2.3.x
```

#### 3.2 下载
```
xiaosi@Qunar:~/opt$ curl -L -O https://download.elastic.co/kibana/kibana/kibana-4.5.1-linux-x64.tar.gz
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 31.5M  100 31.5M    0     0   136k      0  0:03:56  0:03:56 --:--:--  214k
```
#### 3.3 解压
```
tar -zxvf kibana-4.5.1-linux-x64.tar.gz
```
### 4. 安装Marvel

Marvel是Elasticsearch的管理和监控工具，在开发环境下免费使用。它包含了一个叫做Sense的交互式控制台，使用户方便的通过浏览器直接与Elasticsearch进行交互。Elasticsearch线上文档中的很多示例代码都附带一个View in Sense的链接。点击进去，就会在Sense控制台打开相应的实例。安装Marvel不是必须的。

#### 4.1 失败方法 （已丢弃）

Marvel是一个插件，可在Elasticsearch目录中运行以下命令来下载和安装：
```
./bin/plugin -i elasticsearch/marvel/latest
```
但是在运行时遇到如下问题，没有找到 -i 命令：
```
xiaosi@Qunar:/opt/elasticsearch-2.3.3$ ./bin/plugin -i elasticsearch/marvel/latest
ERROR: unknown command [-i]. Use [-h] option to list available commands
```
提示可以使用-h 参数去查看可以使用的命令：
```
xiaosi@Qunar:/opt/elasticsearch-2.3.3$ ./bin/plugin -h
NAME
    plugin - Manages plugins
SYNOPSIS
    plugin <command>
DESCRIPTION
    Manage plugins
COMMANDS
    install    Install a plugin
    remove     Remove a plugin
    list       List installed plugins
NOTES
    [*] For usage help on specific commands please type "plugin <command> -h"
```
我们可以看到我们可以使用install命令来代替-i参数命令：
```
xiaosi@Qunar:/opt/elasticsearch-2.3.3$ sudo ./bin/plugin install elasticsearch/marvel/latest
-> Installing elasticsearch/marvel/latest...
Trying https://download.elastic.co/elasticsearch/marvel/marvel-latest.zip ...
Trying https://search.maven.org/remotecontent?filepath=elasticsearch/marvel/latest/marvel-latest.zip ...
Trying https://oss.sonatype.org/service/local/repositories/releases/content/elasticsearch/marvel/latest/marvel-latest.zip ...
Trying https://github.com/elasticsearch/marvel/archive/latest.zip ...
Trying https://github.com/elasticsearch/marvel/archive/master.zip ...
ERROR: failed to download out of all possible locations..., use --verbose to get detailed information
```
按照提示使用--verbose，查看报错原因：
```
xiaosi@Qunar:/opt/elasticsearch-2.3.3$ sudo ./bin/plugin install elasticsearch/marvel/latest --verbose
-> Installing elasticsearch/marvel/latest...
Trying https://download.elastic.co/elasticsearch/marvel/marvel-latest.zip ...
Failed: FileNotFoundException[https://download.elastic.co/elasticsearch/marvel/marvel-latest.zip]; nested: FileNotFoundException[https://download.elastic.co/elasticsearch/marvel/marvel-latest.zip];
Trying https://search.maven.org/remotecontent?filepath=elasticsearch/marvel/latest/marvel-latest.zip ...
Failed: FileNotFoundException[https://search.maven.org/remotecontent?filepath=elasticsearch/marvel/latest/marvel-latest.zip]; nested: FileNotFoundException[https://search.maven.org/remotecontent?filepath=elasticsearch/marvel/latest/marvel-latest.zip];
Trying https://oss.sonatype.org/service/local/repositories/releases/content/elasticsearch/marvel/latest/marvel-latest.zip ...
Failed: FileNotFoundException[https://oss.sonatype.org/service/local/repositories/releases/content/elasticsearch/marvel/latest/marvel-latest.zip]; nested: FileNotFoundException[https://oss.sonatype.org/service/local/repositories/releases/content/elasticsearch/marvel/latest/marvel-latest.zip];
Trying https://github.com/elasticsearch/marvel/archive/latest.zip ...
Failed: FileNotFoundException[https://github.com/elasticsearch/marvel/archive/latest.zip]; nested: FileNotFoundException[https://github.com/elasticsearch/marvel/archive/latest.zip];
Trying https://github.com/elasticsearch/marvel/archive/master.zip ...
Failed: FileNotFoundException[https://github.com/elasticsearch/marvel/archive/master.zip]; nested: FileNotFoundException[https://github.com/elasticsearch/marvel/archive/master.zip];
ERROR: failed to download out of all possible locations..., use --verbose to get detailed information
```
#### 4.2 正确方法

上面方法已经不在适用了（不知道还有没有解决方法？），现在marvel用Kibana管理，所以第二步先安装Kibana。安装完进行如下操作：
```
xiaosi@Qunar:/opt/elasticsearch-2.3.3$ sudo ./bin/plugin install license
-> Installing license...
Trying https://download.elastic.co/elasticsearch/release/org/elasticsearch/plugin/license/2.3.3/license-2.3.3.zip ...
Downloading .......DONE
Verifying https://download.elastic.co/elasticsearch/release/org/elasticsearch/plugin/license/2.3.3/license-2.3.3.zip checksums if available ...
Downloading .DONE
Installed license into /opt/elasticsearch-2.3.3/plugins/license
```

```
xiaosi@Qunar:/opt/elasticsearch-2.3.3$ sudo ./bin/plugin install marvel-agent
-> Installing marvel-agent...
Trying https://download.elastic.co/elasticsearch/release/org/elasticsearch/plugin/marvel-agent/2.3.3/marvel-agent-2.3.3.zip ...
Downloading ..........DONE
Verifying https://download.elastic.co/elasticsearch/release/org/elasticsearch/plugin/marvel-agent/2.3.3/marvel-agent-2.3.3.zip checksums if available ...
Downloading .DONE
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@     WARNING: plugin requires additional permissions     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
* java.lang.RuntimePermission setFactory
* javax.net.ssl.SSLPermission setHostnameVerifier
See http://docs.oracle.com/javase/8/docs/technotes/guides/security/permissions.html
for descriptions of what these permissions allow and the associated risks.
Continue with installation? [y/N]y
Installed marvel-agent into /opt/elasticsearch-2.3.3/plugins/marvel-agent
```
使用Kibana安装最新版本的marvel：
```
xiaosi@Qunar:~/opt/kibana-4.5.1-linux-x64/bin$ ./kibana plugin --install elasticsearch/marvel/latest
Installing marvel
Attempting to transfer from https://download.elastic.co/elasticsearch/marvel/marvel-latest.tar.gz
Transferring 1597693 bytes....................
Transfer complete
Extracting plugin archive
Extraction complete
Optimizing and caching browser bundles...
Plugin installation complete
```
### 5. 安装总结

步骤|命令
---|---
Step 1: 安装Marvel into Elasticsearch:|bin/plugin install license和bin/plugin install marvel-agent
Step 2: 安装Marvel into Kibana|bin/kibana plugin --install elasticsearch/marvel/latest
Step 3: 启动Elasticsearch and Kibana|bin/elasticsearch和bin/kibana
Step 4: 跳转到http://localhost:5601/app/marvel|
Step 5: 进入[Getting Started Guide](https://www.elastic.co/guide/en/x-pack/current/xpack-monitoring.html).|在没网的情况下运行集群? !img[offline installation instructions](https://www.elastic.co/guide/en/marvel/current/installing-marvel.html#offline-installation).

### 6. 启动elasticsearch，kibana和Marvel

#### 6.1 启动elasticsearch
```
xiaosi@Qunar:~/opt/elasticsearch-2.3.3/bin$ ./elasticsearch
[2016-06-23 22:36:56,431][INFO ][node                     ] [Suprema] version[2.3.3], pid[21803], build[218bdf1/2016-05-17T15:40:04Z]
[2016-06-23 22:36:56,431][INFO ][node                     ] [Suprema] initializing ...
[2016-06-23 22:36:56,895][INFO ][plugins                  ] [Suprema] modules [reindex, lang-expression, lang-groovy], plugins [], sites []
[2016-06-23 22:36:56,913][INFO ][env                      ] [Suprema] using [1] data paths, mounts [[/ (/dev/sda7)]], net usable_space [9.6gb], net total_space [41.5gb], spins? [no], types [ext4]
[2016-06-23 22:36:56,913][INFO ][env                      ] [Suprema] heap size [990.7mb], compressed ordinary object pointers [true]
[2016-06-23 22:36:58,387][INFO ][node                     ] [Suprema] initialized
[2016-06-23 22:36:58,387][INFO ][node                     ] [Suprema] starting ...
[2016-06-23 22:36:58,464][INFO ][transport                ] [Suprema] publish_address {127.0.0.1:9300}, bound_addresses {[::1]:9300}, {127.0.0.1:9300}
[2016-06-23 22:36:58,468][INFO ][discovery                ] [Suprema] elasticsearch/enfSRI_1RoORbk9eIqogQw
[2016-06-23 22:37:01,546][INFO ][cluster.service          ] [Suprema] new_master {Suprema}{enfSRI_1RoORbk9eIqogQw}{127.0.0.1}{127.0.0.1:9300}, reason: zen-disco-join(elected_as_master, [0] joins received)
[2016-06-23 22:37:01,569][INFO ][http                     ] [Suprema] publish_address {127.0.0.1:9200}, bound_addresses {[::1]:9200}, {127.0.0.1:9200}
[2016-06-23 22:37:01,572][INFO ][node                     ] [Suprema] started
[2016-06-23 22:37:01,611][INFO ][gateway                  ] [Suprema] recovered [0] indices into cluster_state
[2016-06-23 22:37:42,722][INFO ][cluster.metadata         ] [Suprema] [.kibana] creating index, cause [api], templates [], shards [1]/[1], mappings [config]
[2016-06-23 22:37:43,056][INFO ][cluster.routing.allocation] [Suprema] Cluster health status changed from [RED] to [YELLOW] (reason: [shards started [[.kibana][0]] ...]).
[2016-06-23 22:37:45,803][INFO ][cluster.metadata         ] [Suprema] [.kibana] create_mapping [index-pattern]
```
在浏览器中输入：http://localhost:9200/
```
{
	name: "Suprema",
	cluster_name: "elasticsearch",
	version: {
		number: "2.3.3",
		build_hash: "218bdf10790eef486ff2c41a3df5cfa32dadcfde",
		build_timestamp: "2016-05-17T15:40:04Z",
		build_snapshot: false,
		lucene_version: "5.5.0"
	},
	tagline: "You Know, for Search"
}
```
#### 6.2 启动kibana
```
xiaosi@Qunar:~$ cd ~/opt/kibana-4.5.1-linux-x64/bin/
xiaosi@Qunar:~/opt/kibana-4.5.1-linux-x64/bin$ ./kibana
  log   [22:37:36.150] [info][status][plugin:kibana] Status changed from uninitialized to green - Ready
  log   [22:37:36.177] [info][status][plugin:elasticsearch] Status changed from uninitialized to yellow - Waiting for Elasticsearch
  log   [22:37:36.181] [info][status][plugin:marvel] Status changed from uninitialized to yellow - Waiting for Elasticsearch
  log   [22:37:36.198] [info][status][plugin:kbn_vislib_vis_types] Status changed from uninitialized to green - Ready
  log   [22:37:36.202] [info][status][plugin:markdown_vis] Status changed from uninitialized to green - Ready
  log   [22:37:36.210] [info][status][plugin:metric_vis] Status changed from uninitialized to green - Ready
  log   [22:37:36.218] [info][status][plugin:spyModes] Status changed from uninitialized to green - Ready
  log   [22:37:37.455] [info][status][plugin:statusPage] Status changed from uninitialized to green - Ready
  log   [22:37:37.462] [info][status][plugin:table_vis] Status changed from uninitialized to green - Ready
  log   [22:37:37.468] [info][listening] Server running at http://0.0.0.0:5601
  log   [22:37:42.513] [info][status][plugin:elasticsearch] Status changed from yellow to yellow - No existing Kibana index found
  log   [22:37:45.762] [info][status][plugin:elasticsearch] Status changed from yellow to green - Kibana index ready
  log   [22:37:45.876] [info][status][plugin:marvel] Status changed from yellow to green - Marvel index ready
```
浏览器中输入： http://0.0.0.0:5601

![](http://img.blog.csdn.net/20160623230216038)

#### 6.3 启动Marvel

浏览器中输入：http://localhost:5601/app/marvel

![](http://img.blog.csdn.net/20160623230233116)



初步安装完毕，以后还需配置一些东西。。。。
