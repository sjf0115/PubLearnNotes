## 1. 现象

Spark 升级到 3.1.3 版本，在本地调试时抛出如下异常：
```java
Exception in thread "main" java.lang.NoSuchFieldError: JAVA_9
	at org.apache.spark.storage.StorageUtils$.<init>(StorageUtils.scala:207)
	at org.apache.spark.storage.StorageUtils$.<clinit>(StorageUtils.scala)
	at org.apache.spark.storage.BlockManagerMasterEndpoint.<init>(BlockManagerMasterEndpoint.scala:109)
	at org.apache.spark.SparkEnv$.$anonfun$create$9(SparkEnv.scala:371)
	at org.apache.spark.SparkEnv$.registerOrLookupEndpoint$1(SparkEnv.scala:311)
	at org.apache.spark.SparkEnv$.create(SparkEnv.scala:359)
	at org.apache.spark.SparkEnv$.createDriverEnv(SparkEnv.scala:189)
	at org.apache.spark.SparkContext.createSparkEnv(SparkContext.scala:277)
	at org.apache.spark.SparkContext.<init>(SparkContext.scala:458)
	at org.apache.spark.SparkContext$.getOrCreate(SparkContext.scala:2672)
	at org.apache.spark.sql.SparkSession$Builder.$anonfun$getOrCreate$2(SparkSession.scala:945)
	at scala.Option.getOrElse(Option.scala:189)
	at org.apache.spark.sql.SparkSession$Builder.getOrCreate(SparkSession.scala:939)
	at com.spark.example.core.base.WordCount.main(WordCount.java:36)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
```

## 2. 分析

我们看到错误提示是在 StorageUtils 类中找不到 JavaVersion 的 JAVA_9 字段：
```java
private StorageUtils$() {
    ...
    // 207行
    if(SystemUtils.isJavaVersionAtLeast(JavaVersion.JAVA_9)) {
        ...
    }
    ...
}
```
JavaVersion 是 commons-lang3 包下的一个枚举类，当前版本是 3.4 版本，只有如下几个枚举值：
```
public enum JavaVersion {
    JAVA_0_9(1.5F, "0.9"),
    JAVA_1_1(1.1F, "1.1"),
    JAVA_1_2(1.2F, "1.2"),
    JAVA_1_3(1.3F, "1.3"),
    JAVA_1_4(1.4F, "1.4"),
    JAVA_1_5(1.5F, "1.5"),
    JAVA_1_6(1.6F, "1.6"),
    JAVA_1_7(1.7F, "1.7"),
    JAVA_1_8(1.8F, "1.8"),
    JAVA_1_9(1.9F, "1.9")
}
```
确实没有 JAVA_9，大概率是版本不一致造成的。通过 commons-lang3 的 ReleaseNotes 了解到，从 3.5 版本开始 Java 9 引入了一个新的版本字符串 Schema，具体细节可以参考 [JEP-223](http://openjdk.java.net/jeps/223)。为了支持 JEP-223 废弃了 JAVA_1_9 枚举类，新引入 JAVA_9 枚举类：
```
public enum JavaVersion {
    JAVA_0_9(1.5F, "0.9"),
    JAVA_1_1(1.1F, "1.1"),
    JAVA_1_2(1.2F, "1.2"),
    JAVA_1_3(1.3F, "1.3"),
    JAVA_1_4(1.4F, "1.4"),
    JAVA_1_5(1.5F, "1.5"),
    JAVA_1_6(1.6F, "1.6"),
    JAVA_1_7(1.7F, "1.7"),
    JAVA_1_8(1.8F, "1.8"),
    /** @deprecated */
    JAVA_1_9(9.0F, "9"),
    JAVA_9(9.0F, "9")
}
```

## 3. 解决方案

commons-lang 包过于老旧导致了上述错误，将 commons-lang3 的至少升级到 3.5 版本即可解决问题：
```xml
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-lang3</artifactId>
    <version>3.5</version>
</dependency>
```
> 是否是由于多个版本冲突导致，可以自己再分析一下
