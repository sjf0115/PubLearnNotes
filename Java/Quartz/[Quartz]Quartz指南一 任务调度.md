

```
package com.sjf.open.job;

import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;

/**
 * Job类
 *
 * Created by xiaosi on 17-6-23.
 */
public class TestJob implements Job{

    // 任务执行代码
    @Override
    public void execute(JobExecutionContext jobExecutionContext) throws JobExecutionException {
        System.out.println("---------------每隔５秒输出");
    }
}
```



测试
```
package com.sjf.open;

import com.sjf.open.job.TestJob;
import org.quartz.CronScheduleBuilder;
import org.quartz.JobBuilder;
import org.quartz.JobDetail;
import org.quartz.Scheduler;
import org.quartz.SchedulerException;
import org.quartz.SchedulerFactory;
import org.quartz.SimpleScheduleBuilder;
import org.quartz.Trigger;
import org.quartz.TriggerBuilder;
import org.quartz.impl.StdSchedulerFactory;

/**
 * Created by xiaosi on 17-6-23.
 */
public class JobTest {
    public static void main(String[] args) throws SchedulerException {
        // 注册作业
        String jobName = "test_job";
        String jobGroup = "test_job_group";
        JobDetail job = JobBuilder.newJob(TestJob.class).withIdentity(jobName, jobGroup).build();

        // Simple触发器
        String triggerName = "simple_trigger";
        String triggerGroup = "test_trigger_group";
        SimpleScheduleBuilder simpleScheduleBuilder = SimpleScheduleBuilder.simpleSchedule().withIntervalInSeconds(5)
                .withRepeatCount(5);
        Trigger simpleTrigger = TriggerBuilder.newTrigger().withIdentity(triggerName, triggerGroup)
                .withSchedule(simpleScheduleBuilder).build();

        // Cron触发器
        triggerName = "cron_trigger";
        triggerGroup = "test_trigger_group";
        CronScheduleBuilder cronScheduleBuilder = CronScheduleBuilder.cronSchedule("0/5 * * ? * *");
        Trigger cronTrigger = TriggerBuilder.newTrigger().withIdentity(triggerName, triggerGroup)
                .withSchedule(cronScheduleBuilder).build();

        // 调度器
        SchedulerFactory schedulerFactory = new StdSchedulerFactory();
        Scheduler scheduler = schedulerFactory.getScheduler();
        scheduler.scheduleJob(job, cronTrigger);
        // 开启调度
        scheduler.start();
        // 关闭调度
        //scheduler.shutdown();

    }
}

```

输出信息
```
---------------每隔５秒输出
20:10:50.700 [main] INFO  org.quartz.core.QuartzScheduler - Scheduler DefaultQuartzScheduler_$_NON_CLUSTERED started.
20:10:55.002 [DefaultQuartzScheduler_QuartzSchedulerThread] DEBUG o.q.simpl.PropertySettingJobFactory - Producing instance of Job 'test_job_group.test_job', class=com.sjf.open.job.TestJob
20:10:55.003 [DefaultQuartzScheduler_Worker-2] DEBUG org.quartz.core.JobRunShell - Calling execute on job test_job_group.test_job
---------------每隔５秒输出
20:10:55.004 [DefaultQuartzScheduler_QuartzSchedulerThread] DEBUG o.quartz.core.QuartzSchedulerThread - batch acquisition of 1 triggers
20:11:00.003 [DefaultQuartzScheduler_QuartzSchedulerThread] DEBUG o.q.simpl.PropertySettingJobFactory - Producing instance of Job 'test_job_group.test_job', class=com.sjf.open.job.TestJob
20:11:00.003 [DefaultQuartzScheduler_Worker-3] DEBUG org.quartz.core.JobRunShell - Calling execute on job test_job_group.test_job
---------------每隔５秒输出
```