

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
