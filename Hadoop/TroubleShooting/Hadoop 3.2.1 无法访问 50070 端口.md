最近在搭建 Hadoop（3.2.1）环境时遇到了一件比较奇葩的问题。Hadoop 配置文件正常，各个守护进程正常启动
```
192:hadoop smartsi$ jps
24980 Jps
24584 SecondaryNameNode
24344 NameNode
24444 DataNode
```
但是启动后无法在浏览器中访问 50070 端口。通过研究发现在 Hadoop 的不同版本中，默认的网络端口可能会有所变化。Hadoop 2.x 中 NameNode 的默认端口为 50070，但是在 Hadoop 3.x
 中 NameNode 的默认端口修改为 9870。所以修改为 `http://localhost:9870/` 查看即可。
