在复杂的任务调度场景中，Quartz Scheduler 以其强大而灵活的特性成为了 Java 开发者的首选。而在 Quartz 的触发机制中，SimpleTrigger 作为最简单直接的触发器类型，常常被开发者低估其价值。今天，让我们一起深入探讨这个看似简单却功能强大的调度工具。

## 1. SimpleTrigger 的历史与定位

SimpleTrigger 是 Quartz 最早的触发器实现之一，简单而明确的一款触发器。与更复杂的 CronTrigger 不同，SimpleTrigger 专注于处理 **基于固定间隔的重复执行** 任务。它的 API 设计直观，学习曲线平缓，特别适合那些不需要复杂日历式调度的场景。

## 2. 核心概念解析

SimpleTrigger 可以满足的调度需求是：在具体的时间点执行一次，或者在具体的时间点执行，并且以指定的间隔重复执行若干次。比如，你有一个trigger，你可以设置它在2026年1月13日的上午11:23:54准时触发，或者在这个时间点触发，并且每隔2秒触发一次，一共重复5次。

根据描述，你可能已经发现了，SimpleTrigger 的属性包括：开始时间、结束时间、重复次数以及重复的间隔：
```java
public interface SimpleTrigger extends Trigger {
    int getRepeatCount();
    long getRepeatInterval();
    int getTimesTriggered();
    TriggerBuilder<SimpleTrigger> getTriggerBuilder();
}

public class SimpleTriggerImpl extends AbstractTrigger<SimpleTrigger> implements SimpleTrigger, CoreTrigger {
    // 首次触发时间
    private Date startTime;
    // 结束时间（可选）
    private Date endTime;
    // 重复次数（0表示一次，-1表示无限）
    private int repeatCount;
    // 重复间隔（毫秒）
    private long repeatInterval;
    ...
}
```

SimpleTrigger 实例通过 TriggerBuilder 设置主要的属性，通过 SimpleScheduleBuilder 设置与 SimpleTrigger 相关的属性，如下所示：
```java
Trigger trigger = TriggerBuilder.newTrigger()
    .withIdentity("trigger4", "group1")
    .startNow() // 立即开始
    .withSchedule(SimpleScheduleBuilder.simpleSchedule()
            .withIntervalInSeconds(10) // 每10秒执行一次
            .repeatForever()) // 重复执行
    .endAt(DateBuilder.dateOf(22, 0, 0)) // 直到22:00
    .build();
```

### 2.1 首次触发时间

首次触发时间可以通过 TriggerBuilder 来设置，你有两个选择：
- 立即触发使用 `startNow()`方法
- 在具体的时间点触发使用 `startAt()` 方法

> 可以使用 DateBuilder 来方便地构造基于开始时间(或终止时间)的调度策略

### 2.2 结束时间

结束时间只能通过 TriggerBuilder 的 `endAt()` 方法来设置在具体的时间点结束。

`endAt()` 方法设置的 endTime 属性值会覆盖设置重复次数的属性值：比如，你可以创建一个 Trigger，在终止时间之前每隔 10 秒执行一次，你不需要去计算在开始时间和终止时间之间的重复次数，只需要设置终止时间并将重复次数设置为 -1 (当然，你也可以将重复次数设置为一个很大的值，并保证该值比 Trigger 在终止时间之前实际触发的次数要大即可)。

### 2.3 重复次数

重复次数，可以是 0、-1 以及正整数。语义详解如下：
| 值 | 含义 | 实际执行次数 |
| :------------- | :------------- | :------------- |
| 0 | 执行一次 | 1 |
| n | 重复n次 | n+1 |
| -1 | 无限重复 | 直到被停止 |

> 需要注意重复次数计算错误的陷阱：`withRepeatCount(5)` 并不意味着执行5次，实际执行次数 = repeatCount + 1 = 6 次

重复次数是与 SimpleTrigger 相关的属性，只能通过 SimpleScheduleBuilder 来设置：
- 设置固定的重复次数使用 `withRepeatCount(int triggerRepeatCount)` 方法
- 设置无限重复执行使用 `repeatForever()` 方法

### 2.4 重复间隔

重复的间隔，必须是 0，或者 long 型的正数。重复间隔也是与 SimpleTrigger 相关的属性，只能通过 SimpleScheduleBuilder 来设置：
- 设置毫秒间隔使用 `withIntervalInMilliseconds(long intervalInMillis)` 方法
- 设置秒间隔使用 `withIntervalInSeconds(int intervalInSeconds)`
- 设置分钟间隔使用 `withIntervalInMinutes(int intervalInMinutes)`
- 设置小时间隔使用 `withIntervalInHours(int intervalInHours)`

```java
// 内置的便捷方法
SimpleScheduleBuilder builder = SimpleScheduleBuilder.simpleSchedule()
    .withIntervalInMilliseconds(500)    // 毫秒
    .withIntervalInSeconds(30)          // 秒
    .withIntervalInMinutes(10)          // 分钟
    .withIntervalInHours(2);            // 小时
```

## 3. 核心使用场景

### 场景一：立即触发，仅执行一次
```java
Trigger trigger1 = TriggerBuilder.newTrigger()
    .withIdentity("trigger1", "group1")
    .startNow() // 立即开始
    .build();
```
> [完整示例](https://github.com/sjf0115/quartz-example/blob/main/quartz-quick-start/src/main/java/com/quartz/example/trigger/simple/SimpleTrigger1Example.java)

### 场景二：立即触发，每10秒执行一次 重复执行5次
```java
Trigger trigger2 = TriggerBuilder.newTrigger()
      .withIdentity("trigger2", "group1")
      .startNow() // 立即开始
      .withSchedule(SimpleScheduleBuilder.simpleSchedule()
              .withIntervalInSeconds(10) // 每10秒执行一次
              .withRepeatCount(5)) // 重复执行5次
      .build();
```
> [完整示例](https://github.com/sjf0115/quartz-example/blob/main/quartz-quick-start/src/main/java/com/quartz/example/trigger/simple/SimpleTrigger2Example.java)

### 场景三：立即触发，每10秒执行一次 无限次重复执行
```java
Trigger trigger3 = TriggerBuilder.newTrigger()
    .withIdentity("trigger3", "group1")
    .startNow() // 立即开始
    .withSchedule(SimpleScheduleBuilder.simpleSchedule()
            .withIntervalInSeconds(10) // 每10秒执行一次
            .repeatForever()) // 无限次重复执行
    .build();
```
> [完整示例](https://github.com/sjf0115/quartz-example/blob/main/quartz-quick-start/src/main/java/com/quartz/example/trigger/simple/SimpleTrigger3Example.java)

### 场景四：立即触发，每10秒执行一次 无限次重复执行直到15:45
```java
Trigger trigger3 = TriggerBuilder.newTrigger()
    .withIdentity("trigger3", "group1")
    .startNow() // 立即开始
    .withSchedule(SimpleScheduleBuilder.simpleSchedule()
            .withIntervalInSeconds(10) // 每10秒执行一次
            .repeatForever()) // 无限次重复执行
    .build();
```
> [完整示例](https://github.com/sjf0115/quartz-example/blob/main/quartz-quick-start/src/main/java/com/quartz/example/trigger/simple/SimpleTrigger4Example.java)

### 场景五：5分钟以后开始触发，仅执行一次

```java
Trigger trigger5 = TriggerBuilder.newTrigger()
    .withIdentity("trigger5", "group1")
    .startAt(DateBuilder.futureDate(5, DateBuilder.IntervalUnit.MINUTE)) // 5分钟以后开始触发
    .withSchedule(SimpleScheduleBuilder.simpleSchedule()
            .withIntervalInSeconds(10) // 每10秒执行一次
            .withRepeatCount(5)) // 重复执行5次
    .build();
```
> [完整示例](https://github.com/sjf0115/quartz-example/blob/main/quartz-quick-start/src/main/java/com/quartz/example/trigger/simple/SimpleTrigger5Example.java)
