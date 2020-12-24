Airflow调度程序监视所有任务和所有DAG，并触发满足依赖关系的任务实例。 在幕后，它会监视并保持与其可能包含的所有DAG对象的文件夹同步，并定期（每分钟左右）检查活动任务以查看是否可以触发。

Airflow调度器为运行Airflow生产环境中持久服务而设计的。要启动它，所有你需要做的是执行Airflow调度器。它将使用`airflow.cfg`中指定的配置。

请注意，如果你在`schedule_interval`设置为1天的配置上运行DAG，如果指定开始时间为`2016-01-01`，那么DAG将在`2016-01-01 T23：59`之后瞬间被触发。 换句话说，一旦它覆盖的时间周期结束，作业实例就会被启动(译者注:如果指定某一天开始运行，实际是在这一天的最后时间才开始触发执行)。

让我们重复一下，The scheduler runs your job one `schedule_interval` AFTER the start date, at the END of the period。

调度器启动一个`airflow.cfg`中指定的执行器实例。如果执行器是`LocalExecutor`，任务将作为子进程执行;如果是`CeleryExecutor`或`MesosExecutor`，远程执行任务。

要启动一个调度器，只需运行如下命令：
```
airflow scheduler
```

### 1. DAG Runs

DAG Run是一个表示DAG实时实例化的对象(A DAG Run is an object representing an instantiation of the DAG in time)。

每个DAG可能有也可能没有一个时间表(schedule)，来通知`DAG Run`的创建方式。`schedule_interval`被定义为DAG参数，并且优先使用以cron表达式作为的`str`或`datetime.timedelta`对象。或者，也可以使用下面这些cron"预设"：

预设|描述|cron表达式
---|---|---
`None`|不用安排(schedule)，仅用于“外部触发”的DAG|
`@once`|安排一次且只有一次|	 
`@hourly`|每一小时运行一次|0 * * * *
`@daily`|在每天0点0分时运行一次|	0 0 * * *
`@weekly`|在每周日0点0分时运行一次|0 0 * * 0
`@monthly`|在每个月的第一天0点0分时运行一次|0 0 1 * *
`@yearly`|在每年1月1日0点0分时运行一次|0 0 1 1 *

DAG将为每个时间表schedule进行实例化，同时为每个时间表创建DAG运行条目。

DAG Run都具有与它们相关联的状态（运行，失败，成功），并通知时间表集合所在的调度器为任务提交进行评估(informs the scheduler on which set of schedules should be evaluated for task submissions.)。如果在DAG运行级别没有元数据，Airflow调度器将有更多的工作去做，以确定应该触发什么任务。在添加新任务，更改DAG的形状时，也可能会产生不必要的处理。
