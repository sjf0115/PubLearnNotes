## 1. 问题

执行如下命令对 Hive 源码进行编译：
```
 mvn clean package -Pdist -DskipTests -Dmaven.javadoc.skip=true
```
出现如下问题：
```
...
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 2.526 s
[INFO] Finished at: 2025-10-03T08:29:59+08:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal on project hive-upgrade-acid: Could not resolve dependencies for project org.apache.hive:hive-upgrade-acid:jar:3.1.3: Could not find artifact org.pentaho:pentaho-aggdesigner-algorithm:jar:5.1.5-jhyde in aliyunmaven (https://maven.aliyun.com/repository/public) -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/DependencyResolutionException
```

## 2. 解决方案

在 maven 的 settings.xml 中添加如下镜像：
```xml
<!-- 阿里云 spring plugin -->
<mirror>
    <id>spring-plugin</id>
    <mirrorOf>*</mirrorOf>
    <name>spring-plugin</name>
    <url>https://maven.aliyun.com/repository/spring-plugin</url>
</mirror>

<!-- 阿里云中央仓库 -->
<mirror>
  <id>aliyun-central</id>
  <mirrorOf>*</mirrorOf>
  <name>阿里云中央仓库</name>
  <url>https://maven.aliyun.com/repository/central</url>
</mirror>

<!-- 阿里云公共仓库 -->
<mirror>
  <id>aliyun-public</id>
  <mirrorOf>*</mirrorOf>
  <name>阿里云公共仓库</name>
  <url>https://maven.aliyun.com/repository/public</url>
</mirror>
```
