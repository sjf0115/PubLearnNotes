## 1. 基础

- [x] [Hive 分桶 Bucket](https://smartsi.blog.csdn.net/article/details/127799255)
- [x] [Hive 排除 SELECT 中某列](https://smartsi.blog.csdn.net/article/details/129073922)
- [x] [Hive 如何实现自定义函数 UDF](https://blog.csdn.net/SunnyYoona/article/details/126211216)
- [x] [深入理解 Hive UDAF](https://smartsi.blog.csdn.net/article/details/127964198)
- [x] [Hive 日期相关函数](https://smartsi.blog.csdn.net/article/details/52987726)
- [x] [Hive 如何使用 Grouping Sets](https://smartsi.blog.csdn.net/article/details/126325198)
- [x] [Hive SORT BY vs ORDER BY vs DISTRIBUTE BY vs CLUSTER BY](https://smartsi.blog.csdn.net/article/details/129000338)
- [ ] [Hive 窗口函数 LEAD、LAG、FIRST_VALUE、LAST_VALUE]()
- [ ] [Hive 分析函数 RANK ROW_NUMBER CUME_DIST CUME_DIST](https://smartsi.blog.csdn.net/article/details/56488568)
- [x] [Hive Union 使用指南](https://smartsi.blog.csdn.net/article/details/60779047)
- [x] [Hive JsonSerde 使用指南](https://smartsi.blog.csdn.net/article/details/70170173)
- [x] [Hive Lateral View 使用指南](https://smartsi.blog.csdn.net/article/details/62894761)
- [ ] [Hive 如何定义窗口]()
- [x] [Hive 实战：位图 Bitmap 系列-bitmap_and 函数实现解析](https://smartsi.blog.csdn.net/article/details/139549497)
- [x] [Hive 实战：位图 Bitmap 系列-group_bitmap UDAF 实现解析](https://smartsi.blog.csdn.net/article/details/139575557)
- [x] [Hive 实战：位图 Bitmap 系列-位图计算函数](https://smartsi.blog.csdn.net/article/details/139701146)
- [X] [Hive 一起了解一下 HiveServer2](https://smartsi.blog.csdn.net/article/details/75322177)
- [x] [Hive 如何启动 HiveServer2](https://smartsi.blog.csdn.net/article/details/75322224)
- [X] [Hive 通过 Jdbc 连接 HiveServer2](https://smartsi.blog.csdn.net/article/details/128402139)
- [x] [Hive 元数据服务 MetaStore](https://smartsi.blog.csdn.net/article/details/124440004)

## 2. 原理

- [ ] [Hive CBO 原理介绍]()

## 3. 调优

- [ ] [Hive 简单查询 FetchTask]()
- [ ] [Hive 启用压缩]()
- [ ] [Hive 本地执行模式]()
- [ ] [Hive ORC 文件格式]()
- [ ] [Hive 公用表表达式 CTE 使用指南](https://smartsi.blog.csdn.net/article/details/129074882)
- [x] [Hive ROW_NUMBER TopN 性能优化](https://smartsi.blog.csdn.net/article/details/129094825)
- [x] [Hive Count Distinct 优化](https://smartsi.blog.csdn.net/article/details/127814412)
- [x] [Hive Join 优化之 Map Join](https://smartsi.blog.csdn.net/article/details/121190775)
- [ ] [Hive Join 优化之 Skewed Join]()

## 4. 实战

- [x] [Hive 安装与配置](https://smartsi.blog.csdn.net/article/details/126198200)
- [x] [在 Zeppelin 中如何使用 Hive](https://smartsi.blog.csdn.net/article/details/125031162)

## 5. 源码

- [x] [Hive 源码解读 准备篇 Debug 讲解](https://smartsi.blog.csdn.net/article/details/128392774)
- [x] [Hive 源码解读 CliDriver HQL 读取与参数解析](https://smartsi.blog.csdn.net/article/details/128462596)
- [x] [Hive 源码解读 CliDriver HQL 语句拆分](https://smartsi.blog.csdn.net/article/details/128607389)
- [x] [Hive 源码解读 CliDriver HQL 命令处理](https://smartsi.blog.csdn.net/article/details/128622970)
- [ ] [Hive 源码解读 CliDriver 变量替换]()
- [ ] [Hive 源码解读 输出控制台]()
- [ ] [Hive 源码解读 CliDriver 命令处理器 CommandProcessor]()
- [ ] [Hive 源码解读 Hook 执行]()
- [x] [Hive 源码解读 Driver 将 HQL 语句转换为 AST](https://smartsi.blog.csdn.net/article/details/128668094)
- [x] [Hive 源码解读 Driver 语义分析器 SemanticAnalyzer](https://smartsi.blog.csdn.net/article/details/128695596)
- [ ] [Hive 源码解读 Driver 将 AST 转换为 QueryBlock]()
  - [ ] [Hive 源码解读 Driver 将 AST 转换为 ResolvedParseTree 解析树]()
  - [ ] [Hive 源码解读 Driver 分析创建表命令]()
  - [ ] [Hive 源码解读 Driver 分析创建视图命令]()
- [ ] [Hive 源码解读 Driver 将 QueryBlock 转换为 OperatorTree 操作树]()
- [ ] [Hive 源码解读 Driver 对 OperatorTree 进行逻辑优化]()
- [ ] [Hive 源码解读 Driver 生成 TaskTree]()
- [ ] [Hive 源码解读 Driver 提交任务作业]()

## 6. TroubleShooting

- [x] [Hive 2.3.4 does not implement the requested interface org.roaringbitmap.BitmapDataProvider](https://smartsi.blog.csdn.net/article/details/139106490)
- [x] [Hive 1.2.2 Unsupported major.minor version 51.0](https://smartsi.blog.csdn.net/article/details/129272590)
- [x] [Hive 2.3.4 SemanticException [Error 10025]: Line 18:7 Expression not in GROUP BY key ‘xxx‘](https://smartsi.blog.csdn.net/article/details/129272452)
- [x] [Hive 3.1.3 编译出错 ldap-client-api:jar:0.1-SNAPSHOT 获取不到](https://smartsi.blog.csdn.net/article/details/128366027)
- [x] [Hive 3.1.2 编译出现 Unknown host snapshots.maven.codehaus.org](https://smartsi.blog.csdn.net/article/details/128360281)
- [x] [Hive 2.3.4 Unable to instantiate org.apache.hadoop.hive.ql.metadata.SessionHiveMetaStoreClient](https://smartsi.blog.csdn.net/article/details/126210823)
- [x] [Hive 2.3.4 Name node is in safe mode. The reported blocks xxx has reached the threshold 0.9990 of to](https://smartsi.blog.csdn.net/article/details/126206405)
