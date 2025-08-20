## 1. 问题

启动 Kafka 集群时遇到如下异常：
```
Error: VM option 'UseG1GC' is experimental and must be enabled via -XX:+UnlockExperimentalVMOptions.
Error: Could not create the Java Virtual Machine.
Error: A fatal exception has occurred. Program will exit.
```
## 2. 分析

从上述异常信息中可以知道：
- JVM 认为你尝试使用的虚拟机选项 `-XX:+UseG1GC` 是一个实验性（Experimental） 功能。
- 为了防止用户无意中使用可能不稳定的实验功能，JVM要求必须显式地“解锁”这些选项。这就是为什么它提示你必须通过 `-XX:+UnlockExperimentalVMOptions` 来启用。
- 直接后果时由于 JVM 参数校验失败，Java 虚拟机根本无法创建，导致 Kafka 服务进程启动失败并退出。

这个问题的根源在于 JVM 版本的变迁 和 Kafka 默认配置的冲突。在这由于我们使用的 Kafka 比较新的版本，其启动脚本（kafka-server-start.sh）中默认的 JVM 参数配置包含了 `-XX:+UseG1GC`，但由于我们使用的是 JDK 8 比较低的版本，所以导致冲突。

## 3. 解决方案

### 3.1 方案1：升级 Java 版本

这是最根本、最推荐的解决方案。

### 3.2 方案2：修改Kafka启动参数（临时或兼容性方案）

如果你因某些原因暂时无法升级 Java，可以修改 Kafka 的启动脚本，增加解锁实验性选项的参数。Kafka 的 JVM 参数通常不直接写在启动脚本 `kafka-server-start.sh` 中，而是在调用的 `kafka-run-class.sh` 脚本中设置。

打开 `$KAFKA_HOME/bin/kafka-server-start.sh` 文件，找到设置 JVM 参数的地方。通常你会在文件末尾附近看到类似这样的代码：
```bash
exec $base_dir/kafka-run-class.sh $EXTRA_ARGS kafka.Kafka "$@"
```

找到 `kafka-run-class.sh` 文件中看到类似这样的代码：
```bash
if [ -z "$KAFKA_JVM_PERFORMANCE_OPTS" ]; then
  KAFKA_JVM_PERFORMANCE_OPTS="-server -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 -XX:+ExplicitGCInvokesConcurrent -XX:MaxInlineLevel=15 -Djava.awt.headless=true"
fi
```
我们只需要修改 `KAFKA_JVM_PERFORMANCE_OPTS` 配置添加 `-XX:+UnlockExperimentalVMOptions` 即可:
```
KAFKA_JVM_PERFORMANCE_OPTS="-server -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 -XX:+ExplicitGCInvokesConcurrent -XX:MaxInlineLevel=15 -Djava.awt.headless=true"
```
