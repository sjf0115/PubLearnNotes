
重要说明：确保已设置 HADOOP_CLASSPATH 环境变量，可以通过运行如下命令进行检查：
```
echo $HADOOP_CLASSPATH
```

在 YARN上 启动 Flink Session

确保已设置 HADOOP_CLASSPATH 环境变量后，就可以在 YARN Session 上启动 Flink 并提交作业：






```
./bin/yarn-session.sh --detached
```







参考：https://ci.apache.org/projects/flink/flink-docs-master/zh/docs/deployment/resource-providers/yarn/
