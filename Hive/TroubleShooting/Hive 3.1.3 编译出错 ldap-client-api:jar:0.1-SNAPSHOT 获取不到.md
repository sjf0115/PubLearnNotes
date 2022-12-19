## 1. 问题

使用 `mvn clean package -Pdist -DskipTests -Dmaven.javadoc.skip=true` 命令打包编译失败：
```
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 05:15 min
[INFO] Finished at: 2022-12-18T20:14:35+08:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal on project hive-service: Could not resolve dependencies for project org.apache.hive:hive-service:jar:3.1.3: Failed to collect dependencies at org.apache.directory.server:apacheds-server-integ:jar:1.5.6 -> org.apache.directory.client.ldap:ldap-client-api:jar:0.1-SNAPSHOT: Failed to read artifact descriptor for org.apache.directory.client.ldap:ldap-client-api:jar:0.1-SNAPSHOT: Could not transfer artifact org.apache.directory.client.ldap:ldap-client-api:pom:0.1-SNAPSHOT from/to rdc-releases-aliyun (https://repo.rdc.aliyun.com/repository/25532-release-U4bww5/): Access denied to: https://repo.rdc.aliyun.com/repository/25532-release-U4bww5/org/apache/directory/client/ldap/ldap-client-api/0.1-SNAPSHOT/ldap-client-api-0.1-SNAPSHOT.pom , ReasonPhrase:Forbidden. -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/DependencyResolutionException
[ERROR]
[ERROR] After correcting the problems, you can resume the build with the command
[ERROR]   mvn <goals> -rf :hive-service
```

## 2. 解决方案

顶层中存在一个 org.apache.directory.client.ldap:ldap-client-api，使用的是 0.1 版本，但 org.apache.directory.server:apacheds-server-integ 中也存在一个 org.apache.directory.client.ldap:ldap-client-api，版本为 0.1-SNAPSHOT，并且因为编译时找不到而失败。可以通过排除此传递依赖项轻松将其删除：
```xml
<!-- apache-directory-clientapi.version = 0.1 -->
<dependency>
  <groupId>org.apache.directory.client.ldap</groupId>
  <artifactId>ldap-client-api</artifactId>
  <version>${apache-directory-clientapi.version}</version>
  <scope>test</scope>
</dependency>

<dependency>
  <groupId>org.apache.directory.server</groupId>
  <artifactId>apacheds-server-integ</artifactId>
  <version>${apache-directory-server.version}</version>
  <scope>test</scope>
  <exclusions>
    <exclusion>
        <groupId>org.apache.directory.client.ldap</groupId>
        <artifactId>ldap-client-api</artifactId>
    </exclusion>
  </exclusions>
</dependency>
```
这个问题在 4.0.0-alpha-1 得到解决，具体可以查看 [HIVE-21777](https://issues.apache.org/jira/browse/HIVE-21777)。
