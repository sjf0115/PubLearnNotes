### 1. only recognizes class file versions up to 52.0

在进入 CMAK UI 界面时报如下异常：
```
2020-10-11 16:09:04,043 - [ERROR] a.a.ActorSystemImpl - Uncaught error from thread [application-akka.actor.default-dispatcher-8]: controllers/routes has been compiled by a more recent version of the Java Runtime (class file version 55.0), this version of the Java Runtime only recognizes class file versions up to 52.0, shutting down JVM since 'akka.jvm-exit-on-fatal-error' is enabled for ActorSystem[application]
java.lang.UnsupportedClassVersionError: controllers/routes has been compiled by a more recent version of the Java Runtime (class file version 55.0), this version of the Java Runtime only recognizes class file versions up to 52.0
	at java.lang.ClassLoader.defineClass1(Native Method)
	at java.lang.ClassLoader.defineClass(ClassLoader.java:763)
	at java.security.SecureClassLoader.defineClass(SecureClassLoader.java:142)
	at java.net.URLClassLoader.defineClass(URLClassLoader.java:467)
	at java.net.URLClassLoader.access$100(URLClassLoader.java:73)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:368)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:362)
	at java.security.AccessController.doPrivileged(Native Method)
	at java.net.URLClassLoader.findClass(URLClassLoader.java:361)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
```
经分析发现是我们的 JDK 版本不对，服务器上只有安装 JDK8，而 CMAK 需要 JDK11 +。所以安装 JDK11，通过如下方式重新启动 CMAK：
```
cmak -Dconfig.file=/opt/cmak/conf/application.conf -Dhttp.port=9001 -java-home /opt/jdk-11/Contents/Home
```
### 2. KeeperErrorCode = Unimplemented

打开 CMAK Web UI，添加 Kafka 集群时报如下错误：
```
Yikes! KeeperErrorCode = Unimplemented for /kafka-manager/mutex Try again.
```
解决方案：主要是ZooKeeper版本太低导致，需要升级到3.5+版本。具体请参考[748](https://github.com/yahoo/CMAK/issues/748)

### 3. bootstrap.server is not a recognized option

```
kafka-console-consumer.sh --bootstrap.server=localhost:9092 --topic=file-connector-example-topic --from-beginning
```
在执行上述命令时抛出如下异常：
```
bootstrap.server is not a recognized option
```
主要原因是：在 2.5.0 版本之前只支持 --broker-list；在 2.5.0 版本之后支持 --bootstrap-server。使用如下命令重新执行：
```
kafka-console-consumer.sh --broker-list=localhost:9092 --topic=file-connector-example-topic --from-beginning
```





...
