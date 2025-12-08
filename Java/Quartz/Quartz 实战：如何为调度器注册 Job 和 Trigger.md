
Quartz 是 Java 领域最受欢迎的任务调度框架之一，广泛应用于定时任务、作业调度等场景。然而，许多开发者在初次使用 Quartz 时，经常会遇到这样一个令人困惑的异常：
```java
org.quartz.JobPersistenceException: The job (group1.job1) referenced by the trigger does not exist.
```

这个错误的核心在于**如何正确地向调度器注册 Job 和 Trigger**。在深入解决方案之前，我们先理解 Quartz 的基本概念：
- **JobDetail**：定义要执行的任务内容，包含任务类、任务数据等元信息
- **Trigger**：定义任务的执行计划，包括何时执行、执行频率等
- **Scheduler**：调度器，负责管理 Job 和 Trigger，并在适当时机触发任务执行

关键点在于：**Trigger 必须关联到一个已存在的 JobDetail**。当调度器接收到一个 Trigger 时，它会检查这个 Trigger 关联的 Job 是否已经注册。

本文将深入探讨 Quartz 的注册机制，提供多种解决方案。

## 1. 同步注册法（推荐）

同步注册法即同时注册 Job 和 Trigger，这是最常用、最简洁的注册方式，适用于大多数场景：
```java
// 1. 调度器
Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

// 2. 任务
JobDetail jobDetail1 = JobBuilder.newJob(MyJob.class)
        .withIdentity("job1", "group1") // 任务名称/任务分组名称
        .build();

// 3. 触发器 不指定任务
Trigger trigger1 = TriggerBuilder.newTrigger()
        .withIdentity("trigger1", "group1") // 触发器名称/触发器分组名称
        .startNow() // 立即开始
        .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                .withIntervalInSeconds(10) // 每10秒执行一次
                .withRepeatCount(5)) // 重复执行5次
        .build();

// 4. 将任务和触发器同时注册到调度器
scheduler.scheduleJob(jobDetail1, trigger1);

// 5. 启动调度器
scheduler.start();
```
同步注册法的要点就是调用 `scheduler.scheduleJob(jobDetail1, trigger1)` 同时完成任务和触发器的注册。

### 优点
- 代码简洁明了
- 自动建立 Job 和 Trigger 的关联
- 原子操作，要么都成功，要么都失败

### 适用场景

- 新任务和触发器的初始注册
- 简单的任务调度场景
- 批量注册任务和触发器

## 2. 分步注册法

分步注册法即分步骤实现任务和触发器的注册，这种方法更灵活，适用于需要动态管理任务的场景：
```java
// 1. 调度器
Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

// 2. 先创建 Job 并注册
JobDetail jobDetail2 = JobBuilder.newJob(MyJob.class)
        .storeDurably()
        .withIdentity("job2", "group1") // 任务名称/任务分组名称
        .build();
scheduler.addJob(jobDetail2, true); // true 表示覆盖已有的 Job

// 3. 创建触发器并关联到已存在的 Job
Trigger trigger2 = TriggerBuilder.newTrigger()
        .withIdentity("trigger2", "group1") // 触发器名称/触发器分组名称
        .startNow() // 立即开始
        .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                .withIntervalInSeconds(10) // 每10秒执行一次
                .withRepeatCount(5)) // 重复执行5次
         .forJob(jobDetail2) // 关联已有的 Job
        // .forJob("job2", "group1")
        // .forJob(JobKey.jobKey("job2", "group1"))
        .build();
scheduler.scheduleJob(trigger2); // 注册触发器

// 4. 启动调度器
scheduler.start();
```
分步注册法的要点就是先调用 `scheduler.addJob(jobDetail2, true)` 完成 Job 的注册，再调用 `scheduler.scheduleJob(trigger2)` 完成触发器的注册。如果只是注册触发器就会出现开头提到的异常。

> 需要注意的是当希望 JobDetail 在没有任何关联的 Trigger 时仍然保留在调度器中时使用，需要添加 `storeDurably()`

### 优点

- 更灵活的任务管理
- 支持一个 Job 关联多个 Trigger
- 适合动态添加/移除 Trigger

### 适用场景

- 需要为同一个任务配置多个执行计划
- 动态任务管理（运行时添加/移除触发器）
- 复杂的调度策略

## 3. 总结

正确注册 Job 和 Trigger 是使用 Quartz 的基础。无论选择哪种方法，记住核心原则：**Trigger 必须关联到一个已注册的 JobDetail**。

> [完整代码](https://github.com/sjf0115/quartz-example/blob/main/quartz-quick-start/src/main/java/com/quartz/example/scheduler/RegisterJobAndTriggerExample.java)
