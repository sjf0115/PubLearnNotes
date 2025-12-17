在现代企业级应用中，定时任务调度是不可或缺的核心功能。从每天凌晨的数据备份，到每周末的报表生成，再到复杂的'工作日早上9点到下午6点每半小时执行一次'的需求——这些都需要强大而灵活的调度能力。Quartz 框架作为 Java 领域最成熟的任务调度解决方案，其 `CronTrigger` 正是为满足这类复杂调度需求而生。

与简单的 `SimpleTrigger` 不同，`CronTrigger` 基于日历概念而非精确的时间间隔。它使用 Unix/Linux 系统中广为人知的 Cron 表达式来定义调度计划，但功能更加强大。

## 1. CronTrigger 基础：Cron 表达式

### 1.1 语法详解

Cron 表达式由 6 或 7 个字段组成（Quartz 支持 7 个字段，包含秒和年）：
```
秒 分 时 日 月 周 年（可选）
* * * * * * *
| | | | | | |
| | | | | | +--- 年 Year (1970-2099) 或留空
| | | | | +----- 周 Day-of-Week (1-7 或 SUN-SAT，1表示星期日)
| | | | +------- 月 Month (1-12 或 JAN-DEC)
| | | +--------- 日 Day-of-Month (1-31)
| | +----------- 小时 Hours (0-23)
| +------------- 分钟 Minutes (0-59)
+--------------- 秒 Seconds (0-59)
```

### 1.2 特殊字符含义

- `*`：所有值
  - 字符 `*` 表示所有值。
  - 例如，在分钟 Minutes 字段中使用表示每分钟都会触发，在小时 Hours 字段中使用表示每小时触发。
- `?`：不指定值
  - 字符 `?` 用在日 Day-of-Month 和周 Day-of-Week 字段中，指 '没有具体的值'。
  - 当两个字段其中一个被指定了值以后，为了避免冲突，需要将另外一个的值设为`?`。
  - 例如，想在每月20日触发调度，不管20号是星期几，只能用如下写法：`0 0 0 20 * ?`，其中周 Day-of-Week 字段只能用 `?`，而不能用 `*`。
- `-`：范围
  - 字符 `-` 用来表示指定范围。
  - 秒和分钟字段可以取0到59的整数，小时字段可以取0到23的整数，日字段(Day-of-Month)可以取1到31的整数，不过你需要注意指定的月份到底有多少天。月字段可以取0到11之间的整数
- `,`：多个值
  - 字符 `,` 表示列出枚举值。
  - 例如，分钟 Minutes 字段中使用 `3,23,43` 表示在第 3 分钟、23 分钟以及 43 分钟触发。
- `/`：增量
  - 字符 `/` 表示增量。
  - 例如，分钟 Minutes 字段使用 '0/15'，表示'在这个小时内，从0分钟开始，每隔15分钟'；如果使用'3/20'，则表示'在这个小时内，从第3分钟开始，每隔20分钟'。
- `L`：最后
  - 字符 `L` 用在日 Day-of-Month 和周 Day-of-Week 字段中，它是 last 的缩写。
  - 用于这两个字段时，含义并不相同。例如，用于日字段，表示这个月的最后一天。用于周字段，表示这一周的最后一天。
  - 但是，如果用于周字段时，前面还有一个值，则表示这个月的最后一个周×× - 例如，`6L` 表示这个月的最后一个周五。
- `W`：最近工作日
  - 字符 `W` 表示离某一天最近的工作日（weekday）。
  - 例如，日 Day-of-Month 字段上使用 `15W` 表示离这个月的15号最近的工作日。
- `#`：第几个星期几
  - 字符 `#` 表示这个月的第 n 个周××。
  - 例如，在周 Day-of-Week 字段上的 `6#3` 或 `FRI#3` 表示这个月的第3个周五。

### 1.3 示例

示例1 - 每隔 5 分钟执行一次：
```
0 0/5 * * * ?
```
示例2 - 每隔5分钟，且在该分钟的第10秒执行（如10:00:10 am, 10:05:10 am等）：
```
10 0/5 * * * ?
```
示例3 - 每周三和周五的10:30, 11:30, 12:30和13:30执行：
```
0 30 10-13 ? * WED,FRI
```
示例4 - 在每个月的第5天和第20天，上午8点到上午10点之间每隔半小时执行。注意：该trigger不会在上午10点执行，只在上午8:00, 8:30, 9:00和9:30执行：
```
0 0/30 8-9 5,20 * ?
```

## 2. CronTrigger 基本操作

CronTrigger 实例可以通过 TriggerBuilder（配置主要属性）和 CronScheduleBuilder（配置 CronTrigger 专有的属性）配置：
```java
Trigger trigger1 = TriggerBuilder.newTrigger()
    .withIdentity("trigger1", "group1")
    .startNow() // 立即开始
    .withSchedule(CronScheduleBuilder.cronSchedule("0 0/2 8-17 * * ?"))
    .build();
```

与 SimpleTrigger 一样，CronTrigger 需要设置首次触发时间 startTime 属性，以及(可选的)结束时间 endTime 属性。

### 2.1 首次触发时间

首次触发时间可以通过 TriggerBuilder 来设置，你有两个选择：
- 立即触发使用 `startNow()`方法
- 在具体的时间点触发使用 `startAt()` 方法

> 可以使用 DateBuilder 来方便地构造基于开始时间(或终止时间)的调度策略

### 2.2 结束时间

结束时间只能通过 TriggerBuilder 的 `endAt()` 方法来设置在具体的时间点结束。

`endAt()` 方法设置的 endTime 属性值会覆盖设置重复次数的属性值：比如，你可以创建一个 Trigger，在终止时间之前每隔 10 秒执行一次，你不需要去计算在开始时间和终止时间之间的重复次数，只需要设置终止时间并将重复次数设置为 -1 (当然，你也可以将重复次数设置为一个很大的值，并保证该值比 Trigger 在终止时间之前实际触发的次数要大即可)。


### 2.3 Cron 表达式

Cron 表达式通常通过 CronScheduleBuilder 的 `cronSchedule` 方法来设置：
```java
Trigger trigger = TriggerBuilder.newTrigger()
    .withIdentity("trigger", "group")
    .startNow() // 立即开始
    .withSchedule(CronScheduleBuilder.cronSchedule("0/10 0-2 * * * ?")) // 每小时的0-2分钟每隔10秒执行一次
    .build();
```

此外还可以通过如下快捷方法设置：
- dailyAtHourAndMinute：每天在指定的小时和分钟触发，适用于需要每日固定时间执行的任务
  ```java
  Trigger trigger1 = TriggerBuilder.newTrigger()
      .withIdentity("trigger1", "group1")
      .startNow() // 立即开始
      .withSchedule(CronScheduleBuilder.dailyAtHourAndMinute(12, 0))// 每天12点触发
      .build();
  ```
- atHourAndMinuteOnGivenDaysOfWeek：在指定的星期几(可以指定多天)的特定时间触发，适用于工作日或特定日期执行的定时任务
  ```java
  Trigger trigger1 = TriggerBuilder.newTrigger()
      .withIdentity("trigger1", "group1")
      .startNow() // 立即开始
      .withSchedule(CronScheduleBuilder.atHourAndMinuteOnGivenDaysOfWeek(12, 0, 2,3))// 每周一二的12点触发
      .build();
  ```
- weeklyOnDayAndHourAndMinute：每周在指定星期几的特定时间触发，适用于每周固定时间执行的任务
  ```java
  Trigger trigger1 = TriggerBuilder.newTrigger()
      .withIdentity("trigger1", "group1")
      .startNow() // 立即开始
      .withSchedule(CronScheduleBuilder.weeklyOnDayAndHourAndMinute(2, 12, 0))// 每周一12点触发
      .build();
  ```
- monthlyOnDayAndHourAndMinute：每月在指定日期的特定时间触发，适用于月度任务
  ```java
  Trigger trigger1 = TriggerBuilder.newTrigger()
      .withIdentity("trigger1", "group1")
      .startNow() // 立即开始
      .withSchedule(CronScheduleBuilder.monthlyOnDayAndHourAndMinute(1, 12, 0))// 每月1号12点触发
      .build();
  ```

## 3. CronTrigger 高级操作

### 3.1 时区支持

对于跨时区应用，时区设置至关重要：

```java
// 设置特定时区的 CronTrigger
TimeZone timeZone = TimeZone.getTimeZone("America/New_York"); // 特定时区
Trigger trigger = TriggerBuilder.newTrigger()
        .withIdentity("trigger", "group")
        .startNow() // 立即开始
        .withSchedule(CronScheduleBuilder
                .cronSchedule("0/10 0-2 * * * ?")
                .inTimeZone(timeZone)
        ) // 每小时的0-2分钟每隔10秒执行一次
        .build();
```

### 3.2 基于日历的排除规则

```java
// 创建排除节假日的触发器
AnnualCalendar holidays = new AnnualCalendar();
Calendar fourthOfJuly = new GregorianCalendar(2024, 6, 4);
holidays.setDayExcluded(fourthOfJuly, true);

scheduler.addCalendar("holidays", holidays, false, false);

Trigger trigger = TriggerBuilder.newTrigger()
    .withIdentity("triggerWithExclude", "group1")
    .withSchedule(CronScheduleBuilder.cronSchedule("0 0 9 ? * MON-FRI")
        .modifiedByCalendar("holidays"))  // 排除节假日
    .build();
```

## 4. 实战

首先定义一个 Job 作业 `CronTriggerJob`：
```java
public class CronTriggerJob implements Job {
    private static final Logger LOG = LoggerFactory.getLogger(CronTriggerJob.class);

    // 定时任务实际执行逻辑
    public void execute(JobExecutionContext context) throws JobExecutionException {
        String jobName = context.getJobDetail().getKey().toString();
        // 执行具体的业务逻辑
        LOG.info("Welcome To Quartz: {}", jobName);
    }
}
```
下面实现一个每小时第0-2分钟内每隔10秒触发调度一次的需求：
```java
public class CronTriggerExample {
    private static final Logger LOG = LoggerFactory.getLogger(CronTriggerExample.class);

    public static void main(String[] args) throws Exception {
        // 1. 调度器
        Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

        // 2. 任务实例
        JobDetail jobDetail = JobBuilder.newJob(CronTriggerJob.class)
                .withIdentity("job", "group") // 任务名称/任务分组名称
                .build();

        // 3. 触发器
        // 立即触发，仅执行一次
        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity("trigger", "group")
                .startNow() // 立即开始
                .withSchedule(CronScheduleBuilder.cronSchedule("0/10 0-2 * * * ?")) // 每小时的0-2分钟每隔10秒执行一次
                .build();

        // 4. 将任务和触发器注册到调度器
        scheduler.scheduleJob(jobDetail, trigger);

        // 5. 启动调度器
        scheduler.start();

        LOG.info("调度器启动成功，任务开始执行...");
    }
}
```
