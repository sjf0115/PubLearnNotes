

```java
...
[INFO] hudi-examples ...................................... SKIPPED
[INFO] hudi-examples-common ............................... SKIPPED
[INFO] hudi-examples-spark ................................ SKIPPED
[INFO] hudi-flink-datasource .............................. SKIPPED
[INFO] hudi-flink1.15.x ................................... SKIPPED
[INFO] hudi-flink ......................................... SKIPPED
[INFO] hudi-examples-flink ................................ SKIPPED
[INFO] hudi-examples-java ................................. SKIPPED
[INFO] hudi-flink1.13.x ................................... SKIPPED
[INFO] hudi-flink1.14.x ................................... SKIPPED
[INFO] hudi-kafka-connect ................................. SKIPPED
[INFO] hudi-flink1.15-bundle .............................. SKIPPED
[INFO] hudi-kafka-connect-bundle .......................... SKIPPED
[INFO] hudi-spark2_2.12 ................................... SKIPPED
[INFO] hudi-spark2-common 0.12.3 .......................... SKIPPED
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 15:59 min
[INFO] Finished at: 2023-08-22T07:01:07+08:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal on project hudi-utilities_2.12: Could not resolve dependencies for project org.apache.hudi:hudi-utilities_2.12:jar:0.12.3: Failed to collect dependencies at io.confluent:kafka-avro-serializer:jar:5.3.4: Failed to read artifact descriptor for io.confluent:kafka-avro-serializer:jar:5.3.4: Could not transfer artifact io.confluent:kafka-avro-serializer:pom:5.3.4 from/to rdc-releases-aliyun (https://repo.rdc.aliyun.com/repository/25532-release-U4bww5/): Access denied to: https://repo.rdc.aliyun.com/repository/25532-release-U4bww5/io/confluent/kafka-avro-serializer/5.3.4/kafka-avro-serializer-5.3.4.pom , ReasonPhrase:Forbidden. -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/DependencyResolutionException
[ERROR]
[ERROR] After correcting the problems, you can resume the build with the command
[ERROR]   mvn <goals> -rf :hudi-utilities_2.12
```


```xml
<repositories>
   <repository>
       <id>confluent</id>
       <url>http://packages.confluent.io/maven/</url>
   </repository>
</repositories>
```


https://www.cnblogs.com/tommyjiang/p/17632338.html
https://zhuanlan.zhihu.com/p/432994050


```java
[INFO] hudi-flink1.13-bundle .............................. SKIPPED
[INFO] hudi-kafka-connect-bundle .......................... SKIPPED
[INFO] hudi-spark2_2.12 ................................... SKIPPED
[INFO] hudi-spark2-common 0.12.3 .......................... SKIPPED
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 15:01 min
[INFO] Finished at: 2023-08-27T21:43:17+08:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal on project hudi-utilities_2.12: Could not resolve dependencies for project org.apache.hudi:hudi-utilities_2.12:jar:0.12.3: Failed to collect dependencies at io.confluent:kafka-avro-serializer:jar:5.3.4: Failed to read artifact descriptor for io.confluent:kafka-avro-serializer:jar:5.3.4: Could not transfer artifact io.confluent:kafka-avro-serializer:pom:5.3.4 from/to tbmirror-all (http://mvnrepo.alibaba-inc.com/mvn/repository): Connect to mvnrepo.alibaba-inc.com:80 [mvnrepo.alibaba-inc.com/59.82.112.94] failed: Operation timed out (Connection timed out) -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/DependencyResolutionException
[ERROR]
[ERROR] After correcting the problems, you can resume the build with the command
[ERROR]   mvn <goals> -rf :hudi-utilities_2.12
localhost:hudi-0.12.3 wy$
```

方案二：
通过网址下载：http://packages.confluent.io/archive/5.3/confluent-5.3.4-2.12.zip
解压后找到以下jar包，上传服务器hadoop1：
- common-config-5.3.4.jar
- common-utils-5.3.4.jar
- kafka-avro-serializer-5.3.4.jar
- kafka-schema-registry-client-5.3.4.jar
然后 install 到 maven 本地仓库
```
mvn install:install-file -DgroupId=io.confluent -DartifactId=common-config -Dversion=5.3.4 -Dpackaging=jar -Dfile=./common-config-5.3.4.jar
mvn install:install-file -DgroupId=io.confluent -DartifactId=common-utils -Dversion=5.3.4 -Dpackaging=jar -Dfile=./common-utils-5.3.4.jar
mvn install:install-file -DgroupId=io.confluent -DartifactId=kafka-avro-serializer -Dversion=5.3.4 -Dpackaging=jar -Dfile=./kafka-avro-serializer-5.3.4.jar
mvn install:install-file -DgroupId=io.confluent -DartifactId=kafka-schema-registry-client -Dversion=5.3.4 -Dpackaging=jar -Dfile=./kafka-schema-registry-client-5.3.4.jar
```

https://blog.csdn.net/weixin_38136584/article/details/128476360




```java
[INFO] hudi-flink1.14.x ................................... SUCCESS [ 43.313 s]
[INFO] hudi-flink1.15.x ................................... SUCCESS [ 43.991 s]
[INFO] hudi-kafka-connect ................................. FAILURE [  7.439 s]
[INFO] hudi-flink1.13-bundle .............................. SKIPPED
[INFO] hudi-kafka-connect-bundle .......................... SKIPPED
[INFO] hudi-spark2_2.12 ................................... SKIPPED
[INFO] hudi-spark2-common 0.12.3 .......................... SKIPPED
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 30:52 min
[INFO] Finished at: 2023-08-28T08:03:52+08:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal com.github.os72:protoc-jar-maven-plugin:3.11.4:run (default) on project hudi-kafka-connect: protoc-jar failed for /Users/wy/software/hudi-0.12.3/hudi-kafka-connect/src/main/resources/ControlMessage.proto. Exit code 2 -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoExecutionException
[ERROR]
[ERROR] After correcting the problems, you can resume the build with the command
[ERROR]   mvn <goals> -rf :hudi-kafka-connect
```
