
### 1. Hadoop脚本

我们通过如下方式运行Hadoop程序时：
```
hadopp jar xxx.jar clalss-name [input] [output]
```

Hadoop的脚本文件.bin/hadoop是Hadoop最终要的脚本，是绝大多数hadoop命令的入口。通过分析该脚本源代码，可知它的执行流程主要如下：
(1) 获得用户命令COMMAND，本例是jar。
(2) 设置JAVA_HOME，JAVA_HEAP_SIZE等变量。
(3) 搜索诸如./build/class等目录，设置类路径CLASSPATH。
(4) 设置诸如HADOOP_LOG_DIR,HADOOP_LOGFILE等变量。
(5) 根据COMMAND的内容，确定需要加载执行的类CLASS和java参数HADOOP_OPTS，如COMMAND为jar时，CLASS=org.apache.hadoop.util.RunJarl。
(6) 设置库路径JAVA_LIBRARY_PATH，主要是加载本地库路径。
(7) 根据前6步设置的变量和得到的类信息，调用java执行类(RunJar)。

我们可以看到运行`hadoop jar`命令其实最终调用了`org.apache.hadoop.util.RunJar`Java类，注意的是如果运行YARN应用程序使用`yarn jar`命令而不是这个命令:
```shell
elif [ "$COMMAND" = "jar" ] ; then
  CLASS=org.apache.hadoop.util.RunJar
  if [[ -n "${YARN_OPTS}" ]] || [[ -n "${YARN_CLIENT_OPTS}" ]]; then
    echo "WARNING: Use \"yarn jar\" to launch YARN applications." 1>&2
  fi
```

```shell
HADOOP_OPTS="$HADOOP_OPTS $HADOOP_CLIENT_OPTS"
#make sure security appender is turned off
HADOOP_OPTS="$HADOOP_OPTS -Dhadoop.security.logger=${HADOOP_SECURITY_LOGGER:-INFO,NullAppender}"
export CLASSPATH=$CLASSPATH
exec "$JAVA" $JAVA_HEAP_MAX $HADOOP_OPTS $CLASS "$@"
```

### 2. RunJar类
