


## 1.

需要下载核心的包，core 与 common，使用 Maven 安装到本地仓库：
```
mvn install:install-file -DgroupId=com.datax -DartifactId=datax-core -Dversion=1.0.0 -Dpackaging=jar -Dfile=datax-core-0.0.1-SNAPSHOT.jar

mvn install:install-file -DgroupId=com.datax -DartifactId=datax-common -Dversion=1.0.0 -Dpackaging=jar -Dfile=datax-common-0.0.1-SNAPSHOT.jar
```
