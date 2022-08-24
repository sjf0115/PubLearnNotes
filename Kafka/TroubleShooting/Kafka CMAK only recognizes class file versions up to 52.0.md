## 1. 现象

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

## 2. 解决方案

经分析发现是我们的 JDK 版本不对，服务器上只有安装 JDK8，而 CMAK 需要 JDK11 +。所以安装 JDK11，可以通过如下方式指定 JDK 11 路径来重新启动 CMAK：
```
cmak -Dconfig.file=/opt/cmak/conf/application.conf -Dhttp.port=9001 -java-home /opt/jdk-11/Contents/Home
```
