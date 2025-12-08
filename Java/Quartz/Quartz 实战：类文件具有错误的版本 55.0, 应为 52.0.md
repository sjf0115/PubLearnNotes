## 1. 问题

使用 2.5.2 版本 Quartz 运行示例程序，出现如下问题：
```java
java: 无法访问org.quartz.impl.StdSchedulerFactory
  错误的类文件: /Users/smartsi/.m2/repository/org/quartz-scheduler/quartz/2.5.2/quartz-2.5.2.jar!/org/quartz/impl/StdSchedulerFactory.class
    类文件具有错误的版本 55.0, 应为 52.0
    请删除该文件或确保该文件位于正确的类路径子目录中。
```

## 2. 解决方案

通过文档可以知道 Quartz 2.5.x 需要 Java 11+。在这切换到 Quartz 2.4.x（Java 8）。
