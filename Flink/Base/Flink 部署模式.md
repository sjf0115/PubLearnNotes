
## 1. 会话模式

会话模式有两种操作模式:
- 附加模式(Attached Mode)：这是默认的操作模式。yarn-session.sh 客户端将 Flink 集群提交给 YARN，但是客户端会继续运行，来跟踪集群的状态。如果集群失败，客户端也会显示错误信息。如果终止客户端，会向集群发出关闭的信号。
- 分离模式(Detached Mode)：该操作模式需要使用 `-d` 或 `——detached` 参数来指定。yarn-session.sh 客户端将 Flink 集群提交给 YARN，然后客户端返回。需要调用客户端或者 YARN 工具的另一个方法来停止 Flink 集群。

会话模式会在 `/tmp/.yarn-properties-<username>` 中创建一个隐藏的 YARN 属性文件。当提交作业时，命令行界面将为集群发现获取该用户名。

在提交 Flink 作业时，还可以在命令行界面中手动指定目标 YARN 集群。举个例子：
```
./bin/flink run -t yarn-session \
  -Dyarn.application.id=application_XXXX_YY \
  ./examples/streaming/TopSpeedWindowing.jar
```
您可以使用以下命令重新连接到 YARN 会话:
```
./bin/yarn-session.sh -id application_XXXX_YY
```
除了通过 `conf/flink-conf.yaml` 传递配置，你也可以在提交时通过 `-Dkey=value` 参数给 `./bin/yarn-session.sh` 客户端传递任何配置。
