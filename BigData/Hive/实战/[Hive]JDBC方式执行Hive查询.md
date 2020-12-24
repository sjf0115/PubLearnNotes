

### 1. HiveServer2配置

```xml
<!-- HiveServer2 -->
<property>
  <name>hive.server2.transport.mode</name>
  <value>binary</value>
  <description>Expects one of [binary, http].Transport mode of HiveServer2.</description>
</property>

<property>
  <name>hive.server2.thrift.bind.host</name>
  <value>xxx</value>
  <description>Bind host on which to run the HiveServer2 Thrift service.</description>
</property>

<property>
  <name>hive.server2.thrift.port</name>
  <value>10000</value>
  <description>Port number of HiveServer2 Thrift interface when hive.server2.transport.mode is 'binary'.</description>
</property>

<!-- Web UI -->
<property>
  <name>hive.server2.webui.host</name>
  <value>xxx</value>
</property>

<property>
  <name>hive.server2.webui.port</name>
  <value>10002</value>
</property>

<property>
  <name>hive.server2.enable.doAs</name>
  <value>false</value>
  <description>Setting this property to true will have HiveServer2 execute Hive operations as the user making the calls to it.</description>
</property>
```

### 2. 启动hiveServer2服务

在使用JDBC执行Hive查询时, 必须首先开启 Hive 的远程服务。

#### 2.1 检查服务是否启动

hiveServer2 的 thrift 的默认端口为 10000:
```
<property>
    <name>hive.server2.thrift.port</name>
    <value>10000</value>
    <description>Port number of HiveServer2 Thrift interface when hive.server2.transport.mode is 'binary'.</description>
</property>
```
通过端口来判断 hiveServer2 是否启动:
```
xiaosi@yoona:~$ sudo netstat -anp | grep 10000
```
#### 1.2 启动服务

如果没有启动hiveServer2服务，通过如下命令启动：
```
xiaosi@yoona:~$ sudo -uxiaosi hive --service hiveserver2 >/dev/null 2>/dev/null &
[1] 11978
```
根据进程ID查看端口号：
```
lsof -i | grep 11978
```


```
[xiaosi@ying]$ ps -aux| grep hiveserver2
Warning: bad syntax, perhaps a bogus '-'? See /usr/share/doc/procps-3.2.8/FAQ
root     20327  0.0  0.0 189268  2936 pts/6    S    17:43   0:00 sudo -uxiaosi hive --service hiveserver2
root     20500  0.0  0.0 189268  2940 pts/6    S    17:43   0:00 sudo -uxiaosi hive --service hiveserver2
root     20603  0.0  0.0 189268  2932 pts/6    S    17:44   0:00 sudo -uxiaosi hive --service hiveserver2
root     20746  0.0  0.0 189268  2936 pts/6    S+   17:44   0:00 sudo -uxiaosi hive --service hiveserver2
40008    21547  0.0  0.0 103240   820 pts/5    R+   17:51   0:00 grep hiveserver2
```




### 2.
