

## 1. beeline.sh

我们可以看出，脚本里主要定义了beeline函数。

beeline主类：`org.apache.hive.beeline.Beeline`
beeline启动jar：`hive-beeline-*.jar`


## 2. cli.sh

Command line interface。命令行界面。cli.sh 脚本主要定义了 cli 函数：
- cli主类：`org.apache.hadoop.hive.cli.CliDriver`

```shell
THISSERVICE=cli
export SERVICE_LIST="${SERVICE_LIST}${THISSERVICE} "

# 设置老版 CLI 作为默认客户端
# 如果没有设置 USE_DEPRECATED_CLI 或者不等于 false 则使用老版 CLI
if [ -z "$USE_DEPRECATED_CLI" ] || [ "$USE_DEPRECATED_CLI" != "false" ]; then
  USE_DEPRECATED_CLI="true"
fi

updateCli() {
  if [ "$USE_DEPRECATED_CLI" == "true" ]; then
    # 老版 CLI
    export HADOOP_CLIENT_OPTS=" -Dproc_hivecli $HADOOP_CLIENT_OPTS "
    CLASS=org.apache.hadoop.hive.cli.CliDriver
    JAR=hive-cli-*.jar
  else
    # 新版 CLI
    export HADOOP_CLIENT_OPTS=" -Dproc_beeline $HADOOP_CLIENT_OPTS -Dlog4j.configurationFile=beeline-log4j2.properties"
    CLASS=org.apache.hive.beeline.cli.HiveCli
    JAR=hive-beeline-*.jar
  fi
}

cli () {
  updateCli
  execHiveCmd $CLASS $JAR "$@"
}

cli_help () {
  updateCli
  execHiveCmd $CLASS $JAR "--help"
}
```

> 参考：[Hive源码解读（2）shell脚本解读](https://www.jianshu.com/p/96e2c2e50bdb)
