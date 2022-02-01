当我们下载一个新的ElaticSearch压缩包并解压，会有一些文件：
```
xiaosi@Qunar:~/opt/elasticsearch-2.3.3$ ls -all
总用量 64
drwxrwxr-x 9 xiaosi xiaosi  4096  6月 23 20:35 .
drwxrwxr-x 6 xiaosi xiaosi  4096  6月 24 13:28 ..
drwxrwxr-x 2 xiaosi xiaosi  4096  6月 23 20:34 bin
drwxrwxr-x 3 xiaosi xiaosi  4096  6月 24 13:38 config
drwxrwxr-x 3 xiaosi xiaosi  4096  6月 23 20:35 data
drwxrwxr-x 2 xiaosi xiaosi  4096  6月 23 20:34 lib
-rw-rw-r-- 1 xiaosi xiaosi 11358  1月 27 20:53 LICENSE.txt
drwxrwxr-x 2 xiaosi xiaosi  4096  6月 23 20:35 logs
drwxrwxr-x 5 xiaosi xiaosi  4096  5月 17 23:48 modules
-rw-rw-r-- 1 xiaosi xiaosi   150  5月 12 21:24 NOTICE.txt
drwxrwxr-x 2 xiaosi xiaosi  4096  6月 23 20:35 plugins
-rw-rw-r-- 1 xiaosi xiaosi  8700  5月 12 21:24 README.textile
```
下面看一下树状目录：
```
├── elasticsearch-2.3.3
│   ├── bin
│   │   ├── elasticsearch
│   │   ├── elasticsearch.bat
│   │   ├── elasticsearch.in.bat
│   │   ├── elasticsearch.in.sh
│   │   ├── elasticsearch-service-mgr.exe
│   │   ├── elasticsearch-service-x64.exe
│   │   ├── elasticsearch-service-x86.exe
│   │   ├── plugin
│   │   ├── plugin.bat
│   │   └── service.bat
│   ├── config
│   │   ├── elasticsearch.yml
│   │   ├── elasticsearch.yml~
│   │   ├── logging.yml
│   │   └── scripts
│   ├── data
│   │   └── elasticsearch
│   ├── lib
│   │   ├── apache-log4j-extras-1.2.17.jar
│   │   ├── commons-cli-1.3.1.jar
│   │   ├── compiler-0.8.13.jar
│   │   ├── compress-lzf-1.0.2.jar
│   │   ├── elasticsearch-2.3.3.jar
│   │   ├── guava-18.0.jar
│   │   ├── HdrHistogram-2.1.6.jar
│   │   ├── hppc-0.7.1.jar
│   │   ├── jackson-core-2.6.6.jar
│   │   ├── jackson-dataformat-cbor-2.6.6.jar
│   │   ├── jackson-dataformat-smile-2.6.6.jar
│   │   ├── jackson-dataformat-yaml-2.6.6.jar
│   │   ├── jna-4.1.0.jar
│   │   ├── joda-convert-1.2.jar
│   │   ├── joda-time-2.8.2.jar
│   │   ├── jsr166e-1.1.0.jar
│   │   ├── jts-1.13.jar
│   │   ├── log4j-1.2.17.jar
│   │   ├── lucene-analyzers-common-5.5.0.jar
│   │   ├── lucene-backward-codecs-5.5.0.jar
│   │   ├── lucene-core-5.5.0.jar
│   │   ├── lucene-grouping-5.5.0.jar
│   │   ├── lucene-highlighter-5.5.0.jar
│   │   ├── lucene-join-5.5.0.jar
│   │   ├── lucene-memory-5.5.0.jar
│   │   ├── lucene-misc-5.5.0.jar
│   │   ├── lucene-queries-5.5.0.jar
│   │   ├── lucene-queryparser-5.5.0.jar
│   │   ├── lucene-sandbox-5.5.0.jar
│   │   ├── lucene-spatial3d-5.5.0.jar
│   │   ├── lucene-spatial-5.5.0.jar
│   │   ├── lucene-suggest-5.5.0.jar
│   │   ├── netty-3.10.5.Final.jar
│   │   ├── securesm-1.0.jar
│   │   ├── snakeyaml-1.15.jar
│   │   ├── spatial4j-0.5.jar
│   │   └── t-digest-3.0.jar
│   ├── LICENSE.txt
│   ├── logs
│   │   ├── elasticsearch_deprecation.log
│   │   ├── elasticsearch_index_indexing_slowlog.log
│   │   ├── elasticsearch_index_search_slowlog.log
│   │   └── elasticsearch.log
│   ├── modules
│   │   ├── lang-expression
│   │   ├── lang-groovy
│   │   └── reindex
│   ├── NOTICE.txt
│   ├── plugins
│   └── README.textile
```
下面看一下具体文件的作用：


属性|描述
---|---
bin|运行ElasticSearch实例和管理插件的一些脚本
config|配置文件位置
lib|库文件位置  


当启动ElasticSearch时，会创建一下文件：

属性|描述
---|---
data|存放数据的位置
logs|存放日志的位置
plugins|存放插件的位置


config文件夹下有两个配置文件：
```
xiaosi@Qunar:~/opt/elasticsearch-2.3.3/config$ ll
总用量 20
drwxrwxr-x 3 xiaosi xiaosi 4096  6月 24 14:28 ./
drwxrwxr-x 9 xiaosi xiaosi 4096  6月 23 20:35 ../
-rw-rw-r-- 1 xiaosi xiaosi 3187  6月 24 13:38 elasticsearch.yml
-rw-rw-r-- 1 xiaosi xiaosi 2571  5月 12 21:24 logging.yml
```
logs文件夹下有四个日志文件：
```
xiaosi@Qunar:~/opt/elasticsearch-2.3.3$ cd logs/
xiaosi@Qunar:~/opt/elasticsearch-2.3.3/logs$ ll
总用量 16
drwxrwxr-x 2 xiaosi xiaosi 4096  6月 23 20:35 ./
drwxrwxr-x 9 xiaosi xiaosi 4096  6月 23 20:35 ../
-rw-rw-r-- 1 xiaosi xiaosi    0  6月 23 20:35 elasticsearch_deprecation.log
-rw-rw-r-- 1 xiaosi xiaosi    0  6月 23 20:35 elasticsearch_index_indexing_slowlog.log
-rw-rw-r-- 1 xiaosi xiaosi    0  6月 23 20:35 elasticsearch_index_search_slowlog.log
-rw-rw-r-- 1 xiaosi xiaosi 7976  6月 23 23:08 elasticsearch.log

```
备注：     

elasticsearch环境相关的配置，例如jvm参数等的设置不是在上面的config文件夹里面，而是在bin下面，如果使用的是linux，可以在elasticsearch.in.sh里面配置，如果是win，那么直接打开elasticsearch.bat编辑配置就行。











