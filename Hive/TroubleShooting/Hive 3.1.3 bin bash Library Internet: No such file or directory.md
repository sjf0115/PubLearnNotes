
## 1. 问题

提交 Hive SQL 运行时发现如下异常：
```
Application application_1754408184889_0001 failed 2 times due to AM Container for appattempt_1754408184889_0001_000002 exited with exitCode: 127
Failing this attempt.Diagnostics: [2025-08-05 23:43:16.172]Exception from container-launch.
Container id: container_1754408184889_0001_02_000001
Exit code: 127
[2025-08-05 23:43:16.173]Container exited with a non-zero exit code 127. Error file: prelaunch.err.
Last 4096 bytes of prelaunch.err :
Last 4096 bytes of stderr :
/bin/bash: /Library/Internet: No such file or directory
[2025-08-05 23:43:16.173]Container exited with a non-zero exit code 127. Error file: prelaunch.err.
Last 4096 bytes of prelaunch.err :
Last 4096 bytes of stderr :
/bin/bash: /Library/Internet: No such file or directory
For more detailed output, check the application tracking page: http://192.168.5.132:8088/cluster/app/application_1754408184889_0001 Then click on links to logs of each attempt.
. Failing the application.
```
从错误日志来看，这是一个典型的 YARN 应用程序管理器(AM)容器启动失败的问题，具体表现为：
- 关键错误信息：`/bin/bash: /Library/Internet: No such file or directory`
- 这表明系统尝试执行一个路径中包含空格的路径 `/Library/Internet...` 但失败了

## 2. 分析

从上述异常信息可以看到应该是使用的 macOS 自带的 Java 默认安装路径：
```bash
/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Home
```
> 不推荐用于 Hadoop/Hive

一般用的比较多的时 Oracle JDK 默认安装路径：
```bash
/Library/Java/JavaVirtualMachines/jdk<version>.jdk/Contents/Home
```

猜测是由于没有配置 JAVA_HOME 导致使用了默认路径，所以需要在 Hadoop 配置文件 `hadoop-env.sh` 中设置 JAVA_HOME：
```bash
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-1.8.jdk/Contents/Home
```
