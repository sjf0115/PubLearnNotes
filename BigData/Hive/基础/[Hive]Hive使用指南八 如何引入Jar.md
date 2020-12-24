### 1. Add Jar

第一种是最常见也是不太友好的的方式是使用`ADD JAR(s)`语句，之所以说是不招人喜欢是，通过该方式添加的jar文件只存在于当前会话中，当会话关闭后不能够继续使用该jar文件，最常见的问题是创建了永久函数到metastore中，再次使用该函数时却提示ClassNotFoundException。所以使用该方式每次都要使用ADD JAR(s)语句添加相关的jar文件到Classpath中。
