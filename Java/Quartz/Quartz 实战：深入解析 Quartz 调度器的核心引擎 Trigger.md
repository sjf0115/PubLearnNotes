在分布式任务调度领域，Quartz 作为 Java 生态系统中最成熟、应用最广泛的调度框架，其核心设计理念围绕两个基本概念展开：**Job**（定义要执行的任务）和**Trigger**（定义何时执行任务）。如果说 Job 是"做什么"，那么 Trigger 就是"何时做"——这个"何时"的复杂性，正是Quartz Trigger设计的精妙所在。

## 1. Trigger 的基本架构：不仅仅是时间表达式

### 1.1 Trigger 定义

```java
public interface Trigger extends Serializable, Cloneable, Comparable<Trigger> {

    TriggerKey getKey();
    JobKey getJobKey();
    String getDescription();
    String getCalendarName();
    JobDataMap getJobDataMap();

    // 优先级
    int getPriority();

    boolean mayFireAgain();

    // 时间
    Date getStartTime();
    Date getEndTime();
    Date getNextFireTime();
    Date getPreviousFireTime();
    Date getFireTimeAfter(Date var1);
    Date getFinalFireTime();

    int getMisfireInstruction();
    TriggerBuilder<? extends Trigger> getTriggerBuilder();
    ScheduleBuilder<? extends Trigger> getScheduleBuilder();
    ...
}
```
trigger的公共属性有：

jobKey属性：当trigger触发时被执行的job的身份；
startTime属性：设置trigger第一次触发的时间；该属性的值是java.util.Date类型，表示某个指定的时间点；有些类型的trigger，会在设置的startTime时立即触发，有些类型的trigger，表示其触发是在startTime之后开始生效。比如，现在是1月份，你设置了一个trigger–“在每个月的第5天执行”，然后你将startTime属性设置为4月1号，则该trigger第一次触发会是在几个月以后了(即4月5号)。
endTime属性：表示trigger失效的时间点。比如，”每月第5天执行”的trigger，如果其endTime是7月1号，则其最后一次执行时间是6月5号。

优先级(priority)
如果你的trigger很多(或者Quartz线程池的工作线程太少)，Quartz可能没有足够的资源同时触发所有的trigger；这种情况下，你可能希望控制哪些trigger优先使用Quartz的工作线程，要达到该目的，可以在trigger上设置priority属性。比如，你有N个trigger需要同时触发，但只有Z个工作线程，优先级最高的Z个trigger会被首先触发。如果没有为trigger设置优先级，trigger使用默认优先级，值为5；priority属性的值可以是任意整数，正数、负数都可以。

注意：只有同时触发的trigger之间才会比较优先级。10:59触发的trigger总是在11:00触发的trigger之前执行。

注意：如果trigger是可恢复的，在恢复后再调度时，优先级与原trigger是一样的。


错过触发(misfire)
trigger还有一个重要的属性misfire；如果scheduler关闭了，或者Quartz线程池中没有可用的线程来执行job，此时持久性的trigger就会错过(miss)其触发时间，即错过触发(misfire)。不同类型的trigger，有不同的misfire机制。它们默认都使用“智能机制(smart policy)”，即根据trigger的类型和配置动态调整行为。当scheduler启动的时候，查询所有错过触发(misfire)的持久性trigger。然后根据它们各自的misfire机制更新trigger的信息。当你在项目中使用Quartz时，你应该对各种类型的trigger的misfire机制都比较熟悉，这些misfire机制在JavaDoc中有说明。关于misfire机制的细节，会在讲到具体的trigger时作介绍。

每个 Trigger 实例都包含三个关键标识属性：
```java
// Trigger的唯一标识三元组
JobKey jobKey = trigger.getJobKey();  // 关联的Job
String name = trigger.getKey().getName();  // Trigger名称
String group = trigger.getKey().getGroup(); // Trigger分组
```
这种设计允许灵活的 Trigger 管理，支持按组批量操作，也避免了命名冲突。

### 1.2 Trigger状态生命周期

理解 Trigger 的状态流转对故障排查至关重要：
- **WAITING**: 等待触发
- **ACQUIRED**: 已被工作线程获取
- **EXECUTING**: 正在执行关联的Job
- **COMPLETE**: 执行完成
- **PAUSED**: 暂停状态
- **BLOCKED**: 因 JobStore 锁定而阻塞
- **ERROR**: 发生错误

## 2. Trigger 类型

### 2.1 SimpleTrigger：精确控制的简单调度

SimpleTrigger 可以满足的调度需求是：在具体的时间点执行一次，或者在具体的时间点执行，并且以指定的间隔重复执行若干次。比如，你有一个trigger，你可以设置它在2015年1月13日的上午11:23:54准时触发，或者在这个时间点触发，并且每隔2秒触发一次，一共重复5次。

根据描述，你可能已经发现了，SimpleTrigger 的属性包括：开始时间、结束时间、重复次数以及重复的间隔。这些属性的含义与你所期望的是一致的，只是关于结束时间有一些地方需要注意。


```java
// 创建立即开始，每10秒执行一次，共执行5次的触发器
SimpleTrigger trigger = TriggerBuilder.newTrigger()
    .withIdentity("trigger1", "group1")
    .startNow()
    .withSchedule(SimpleScheduleBuilder.simpleSchedule()
        .withIntervalInSeconds(10)
        .withRepeatCount(4))
    .build();
```
**适用场景**：固定间隔的简单任务，如每小时的报表生成、定时数据同步等。

### 2.2 CronTrigger：基于日历的复杂调度
```java
// 使用Cron表达式创建触发器
CronTrigger trigger = TriggerBuilder.newTrigger()
    .withIdentity("trigger2", "group1")
    .withSchedule(CronScheduleBuilder.cronSchedule("0 0 12 ? * WED"))
    .build();
```
**Cron表达式威力**：
- `0 0 12 * * ?` 每天中午12点
- `0 15 10 ? * MON-FRI` 工作日早上10:15
- `0 0/5 14,18 * * ?` 每天下午2点到2:55和6点到6:55，每5分钟

### 2.3 CalendarIntervalTrigger：考虑日历差异的间隔触发
```java
// 每月执行一次，自动处理月份天数差异
CalendarIntervalTrigger trigger = TriggerBuilder.newTrigger()
    .withIdentity("trigger3")
    .withSchedule(CalendarIntervalScheduleBuilder.calendarIntervalSchedule()
        .withIntervalInMonths(1))
    .build();
```
**优势**：自动处理不同月份天数、闰年等日历差异，适合月度报告、季度汇总等场景。

### 2.4 DailyTimeIntervalTrigger：精细控制每日时间段
```java
// 工作日每30分钟执行一次，仅在9:00-17:00之间
DailyTimeIntervalTrigger trigger = TriggerBuilder.newTrigger()
    .withSchedule(DailyTimeIntervalScheduleBuilder.dailyTimeIntervalSchedule()
        .startingDailyAt(TimeOfDay.hourAndMinuteOfDay(9, 0))
        .endingDailyAt(TimeOfDay.hourAndMinuteOfDay(17, 0))
        .onDaysOfTheWeek(MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY)
        .withIntervalInMinutes(30))
    .build();
```

## 三、高级特性与最佳实践

### 3.1 Misfire处理策略：当调度错过时
Misfire是调度器必须面对的现实问题。Quartz为每种Trigger提供了丰富的misfire策略：

```java
// 设置CronTrigger的misfire策略
CronTrigger trigger = TriggerBuilder.newTrigger()
    .withSchedule(CronScheduleBuilder.cronSchedule("0 0 12 * * ?")
        .withMisfireHandlingInstructionFireAndProceed())  // 立即触发一次然后继续正常调度
    .build();

// SimpleTrigger的常见策略
SimpleTrigger simpleTrigger = TriggerBuilder.newTrigger()
    .withSchedule(SimpleScheduleBuilder.simpleSchedule()
        .withMisfireHandlingInstructionNextWithExistingCount())  // 以现有计数继续
    .build();
```

**策略选择指南**：
- `withMisfireHandlingInstructionFireNow()`：立即执行错过的一次
- `withMisfireHandlingInstructionIgnoreMisfires()`：忽略错过，尽快执行所有错过的
- `withMisfireHandlingInstructionNextWithRemainingCount()`：等待下一次调度

### 3.2 优先级机制：控制并发竞争
```java
// 设置Trigger优先级（1-10，默认5）
Trigger trigger = TriggerBuilder.newTrigger()
    .withPriority(7)  // 较高优先级
    .build();
```
当多个Trigger同时触发时，高优先级的Trigger将优先获得执行资源。

### 3.3 数据传递与状态保持
```java
// 通过JobDataMap传递参数
JobDataMap dataMap = new JobDataMap();
dataMap.put("server", "production-db");
dataMap.put("retryCount", 3);

Trigger trigger = TriggerBuilder.newTrigger()
    .usingJobData(dataMap)
    .build();
```


http://ifeve.com/quartz-tutorial-04-trigger/
