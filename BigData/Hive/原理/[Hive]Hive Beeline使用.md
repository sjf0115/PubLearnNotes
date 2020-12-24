
```
sudo -uxiaosi bin/beeline
```

```
<property>
  <name>hive.server2.enable.doAs</name>
  <value>false</value>
</property>
```

hive.server2.enable.doAs设置成false则，yarn作业获取到的hiveserver2用户都为hive用户。

设置成true则为实际的用户名
```
[root@hadoop ~]# beeline
which: no hbase in (/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/hadoop/bin:/usr/local/hive/bin:/usr/pgsql-9.4/bin:/root/bin)
ls: cannot access /usr/local/hive/lib/hive-jdbc-*-standalone.jar: No such file or directory
Beeline version 2.1.0-SNAPSHOT by Apache Hive
```

```
hive-jdbc-*-standalone.jar has moved from ${HIVE_HOME}/lib to ${HIVE_HOME}/jdbc. And this file isn't necessary to execution of beeline.
So, I will remove confirmation of this file in beeline.
```
