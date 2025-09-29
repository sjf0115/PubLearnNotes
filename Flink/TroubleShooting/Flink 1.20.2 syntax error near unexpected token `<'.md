## 1. 问题

在使用 `sh bin/start-cluster.sh` 启动 1.20.2 版本的 Flink 集群时，遇到如下问题：
```
smarsi:flink-1.20.2 smartsi$ sh bin/start-cluster.sh
/opt/workspace/flink-1.20.2/bin/config.sh: line 32: syntax error near unexpected token `<'
/opt/workspace/flink-1.20.2/bin/config.sh: line 32: `    done < <(find "$FLINK_LIB_DIR" ! -type d -name '*.jar' -print0 | sort -z)'
Starting cluster.
bin/start-cluster.sh: line 48: /jobmanager.sh: No such file or directory
bin/start-cluster.sh: line 53: TMWorkers: command not found
```
## 2. 分析

上述问题是典型的 Bash 特有语法，在非 Bash shell 中运行的问题。`< <(...)` 是进程替换（process substitution）语法，只在 Bash 中支持，但在其他 shell（如 dash）中不支持。

## 3. 解决方案

第一种方式可以使用 Bash 明确启动：
```
smarsi:flink-1.20.2 smartsi$ bash bin/start-cluster.sh
Starting cluster.
Starting standalonesession daemon on host smarsi.
Starting taskexecutor daemon on host smarsi.
smarsi:flink-1.20.2 smartsi$
```
或者使用如下方式直接执行，使用文件头指定的解释器：
```
smarsi:flink-1.20.2 smartsi$ ./bin/start-cluster.sh
Starting cluster.
Starting standalonesession daemon on host smarsi.
Starting taskexecutor daemon on host smarsi.
```
使用这种方式需要确保脚本有执行权限：
```
chmod +x bin/start-cluster.sh
chmod +x bin/config.sh
```
