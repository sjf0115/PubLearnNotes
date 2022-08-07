

### 1. Add Jar

第一种是最常见也是不太友好的的方式是使用 add jar 语句，之所以说是不招人喜欢是，通过该方式添加的 jar 文件只存在于当前会话中。当会话关闭后不能够继续使用该 jar 文件，最常见的问题是创建了永久函数到 metastore 中，再次使用该函数时却提示 ClassNotFoundException。所以使用该方式每次都要使用 add jar 语句添加相关的 jar 文件到 Classpath 中。




参考：
- https://my.oschina.net/cjun/blog/494692
- https://chetnachaudhari.github.io/2016-02-16/how-to-add-auxiliary-jars-in-hive/
- https://www.cnblogs.com/Dhouse/p/7228557.html
