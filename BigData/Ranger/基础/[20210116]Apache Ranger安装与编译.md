
```
sudo tar -zxvf apache-ranger-2.1.0.tar.gz -C /opt/
```

> 需要检查是否已经安装了 Git、Maven 以及 Python2，注意不能安装 Python3

```
mvn clean compile package assembly:assembly install -DskipTests=true -Drat.skip=true -Dmaven.test.skip=true
```
由于编译时间比较长，可以放后台执行：
```
nohup mvn clean compile package assembly:assembly install -DskipTests=true -Drat.skip=true -Dmaven.test.skip=true > maven.log &
```
编译完成后，在当前 target 目下会生成对应的 tar 文件，如下所示：

![]()

安装并启动ranger-admin

修改配置文件
关于数据库安装，权限设置等，本文不再展开。

进入 target 目录，解压 ranger-1.2.0-admin.tar.gz 包：
```
cd /opt/apache-ranger-1.2.0/target/
tar -zxvf ranger-1.2.0-admin.tar.gz -C /opt
```

修改配置文件 install.properties：
```

```







...
