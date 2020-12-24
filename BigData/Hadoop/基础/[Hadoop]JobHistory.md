

在mapred-site.xml下添加如下配置
```
<property>
    <name>mapreduce.jobhistory.address</name>
    <value>xxx:10020</value>
    <description>MapReduce JobHistory Server IPC host:port</description>
</property>

<property>
    <name>mapreduce.jobhistory.webapp.address</name>
    <value>xxx:19888</value>
    <description>MapReduce JobHistory Server Web UI host:port</description>
</property>

<property>
    <name>mapreduce.jobhistory.intermediate-done-dir</name>
    <value>/job-history/intermediate-done</value>
</property>

<property>
    <name>mapreduce.jobhistory.done-dir</name>
    <value>/job-history/done</value>
</property>
```

启动服务
```
sbin/mr-jobhistory-daemon.sh start historyserver
```
history-server启动之后，在HDFS上会生成两个目录：
```
xiaosi@yoona:~/opt/hadoop-2.7.3$ hadoop fs -ls /job-history
Found 2 items
drwxrwx---   - xiaosi supergroup          0 2017-01-23 10:38 /job-history/done
drwxrwxrwt   - xiaosi supergroup          0 2017-01-23 10:38 /job-history/intermediate-done

```
mapreduce.jobhistory.done-dir(/job-history/done): 由MR JobHistory Server管理的历史文件目录(已完成作业信息)

mapreduce.jobhistory.intermediate-done-dir(/job-history/done_intermediate): 由MapReduce程序正在写入的历史文件目录.(正在运行作业信息)


可以通过浏览器访问WEBUI: 

http://localhost:19888/jobhistory

