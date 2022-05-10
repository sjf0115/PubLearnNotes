


kafka 开启 JMX 有 2 种方式：
- 启动 kafka 时增加 JMX_PORT=9999，即 JMX_PORT=9999 bin/kafka-server-start.sh -daemon config/server.properties
- 修改 kafka-run-class.sh 脚本，第一行增加 JMX_PORT=9999 即可。

事实上这两种配置方式背后的原理是一样的，我们看一下 kafka 的启动脚本 kafka-server-start.sh 的最后一行 exec $base_dir/kafka-run-class.sh $EXTRA_ARGS kafka.Kafka "$@"，实际上就是调用 kafka-run-class.sh 脚本，其中有一段这样的内容：
```shell
# JMX port to use
if [  $JMX_PORT ]; then
  KAFKA_JMX_OPTS="$KAFKA_JMX_OPTS -Dcom.sun.management.jmxremote.port=$JMX_PORT "
fi
```
所以，本质是给参数 JMX_PORT 赋值，第二种方式在脚本的第一行增加 JMX_PORT=9999，$JMX_PORT 就能取到值；而第一种方式有点逼格，本质是设置环境变量然后执行启动脚本，类似下面这种方式给 JMX_PORT 赋值：
```
export JMX_PORT=9999
bin/kafka-server-start.sh -daemon config/server.properties
```
JMX 所有相关参数都在脚本 kafka-run-class.sh 中，如下所示：
```shell
# JMX settings
if [ -z "$KAFKA_JMX_OPTS" ]; then
  KAFKA_JMX_OPTS="-Dcom.sun.management.jmxremote -Djava.rmi.server.hostname=10.0.55.229 -Dcom.sun.management.jmxremote.authenticate=false  -Dcom.sun.management.jmxremote.ssl=false "
fi

# JMX port to use
if [  $JMX_PORT ]; then
  KAFKA_JMX_OPTS="$KAFKA_JMX_OPTS -Dcom.sun.management.jmxremote.port=$JMX_PORT "
fi
```


https://medium.com/@abdullahtrmn/enable-kafka-jmx-port-53bc95271e12
https://www.jianshu.com/p/de4b4cbb0f3c
https://honeypps.com/mq/how-to-monitor-kafka-with-jmx/
