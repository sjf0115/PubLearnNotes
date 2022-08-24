## 1. 现象

```
kafka-console-consumer.sh --bootstrap.server=localhost:9092 --topic=file-connector-example-topic --from-beginning
```
在执行上述命令时抛出如下异常：
```
bootstrap.server is not a recognized option
```

## 2. 解决方案

主要原因是：在 2.5.0 版本之前只支持 --broker-list；在 2.5.0 版本之后支持 --bootstrap-server。使用如下命令重新执行：
```
kafka-console-consumer.sh --broker-list=localhost:9092 --topic=file-connector-example-topic --from-beginning
```
