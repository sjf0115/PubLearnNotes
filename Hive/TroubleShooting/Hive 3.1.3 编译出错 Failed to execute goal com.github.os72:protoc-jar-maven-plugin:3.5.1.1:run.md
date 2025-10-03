## 1. 问题

执行如下命令对 Hive 源码进行编译：
```
 mvn clean package -Pdist -DskipTests -Dmaven.javadoc.skip=true
```
出现如下问题：
```
...
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 44.457 s
[INFO] Finished at: 2025-10-03T08:42:48+08:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal com.github.os72:protoc-jar-maven-plugin:3.5.1.1:run (default) on project hive-standalone-metastore: Error resolving artifact: com.google.protobuf:protoc:2.5.0: Could not find artifact com.google.protobuf:protoc:exe:osx-aarch_64:2.5.0 in spring-plugin (https://maven.aliyun.com/repository/spring-plugin)
[ERROR]
[ERROR] Try downloading the file manually from the project website.
[ERROR]
[ERROR] Then, install it using the command:
[ERROR]     mvn install:install-file -DgroupId=com.google.protobuf -DartifactId=protoc -Dversion=2.5.0 -Dclassifier=osx-aarch_64 -Dpackaging=exe -Dfile=/path/to/file
[ERROR]
[ERROR] Alternatively, if you host your own repository you can deploy the file there:
[ERROR]     mvn deploy:deploy-file -DgroupId=com.google.protobuf -DartifactId=protoc -Dversion=2.5.0 -Dclassifier=osx-aarch_64 -Dpackaging=exe -Dfile=/path/to/file -Durl=[url] -DrepositoryId=[id]
[ERROR]
[ERROR]
[ERROR]   com.google.protobuf:protoc:exe:2.5.0
[ERROR]
[ERROR] from the specified remote repositories:
[ERROR]   spring-plugin (https://maven.aliyun.com/repository/spring-plugin, releases=true, snapshots=true),
[ERROR]   alimaven (http://maven.aliyun.com/nexus/content/groups/public/, releases=true, snapshots=false)
[ERROR] -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoExecutionException
[ERROR]
[ERROR] After correcting the problems, you can resume the build with the command
[ERROR]   mvn <goals> -rf :hive-standalone-metastore
```

## 2. 解决方案

可以使用如下命令完成编译：
```
 mvn clean package -Pdist -DskipTests -Dmaven.javadoc.skip=true -Dos.arch=x86_6
```
`-Dos.arch=x86_6` 这个参数强制让 Maven 认为当前系统是 x86_64 架构，从而下载 osx-x86_64 版本的 protoc 二进制文件。
