经过前两篇文章的简单介绍之后，我们安装了自己的AirFlow以及简单了解了DAG的定义文件．现在我们要实现自己的一个DAG．

### 1. 启动Web服务器

使用如下命令启用:
```
airflow webserver
```
现在可以通过将浏览器导航到启动Airflow的主机上的8080端口来访问Airflow UI，例如：http://localhost:8080/admin/

![img](http://img.blog.csdn.net/20170802173129848?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

**备注**

```
Airflow附带了许多示例DAG。 请注意，在你自己的`dags_folder`中至少有一个DAG定义文件之前，这些示例可能无法正常工作。你可以通过更改`airflow.cfg`中的`load_examples`设置来隐藏示例DAG。
```

### 2. 第一个AirFlow DAG

现在一切都准备好了，我们开始写一些代码，来实现我们的第一个DAG。 我们将首先创建一个Hello World工作流程，其中除了向日志发送"Hello world！"之外什么都不做。

创建你的`dags_folder`，那就是你的DAG定义文件存储目录---`$AIRFLOW_HOME/dags`。在该目录中创建一个名为`hello_world.py`的文件。
```
AIRFLOW_HOME
├── airflow.cfg
├── airflow.db
├── airflow-webserver.pid
├── dags
│   ├── hello_world.py
│   └── hello_world.pyc
└── unittests.cfg
```
将以下代码添加到`dags/hello_world.py`中:
```python
# -*- coding: utf-8 -*-

import airflow
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from datetime import timedelta

#-------------------------------------------------------------------------------
# these args will get passed on to each operator
# you can override them on a per-task basis during operator initialization

default_args = {
    'owner': 'jifeng.si',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(2),
    'email': ['1203745031@qq.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'adhoc':False,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'trigger_rule': u'all_success'
}

#-------------------------------------------------------------------------------
# dag

dag = DAG(
    'example_hello_world_dag',
    default_args=default_args,
    description='my first DAG',
    schedule_interval=timedelta(days=1))

#-------------------------------------------------------------------------------
# first operator

date_operator = BashOperator(
    task_id='date_task',
    bash_command='date',
    dag=dag)

#-------------------------------------------------------------------------------
# second operator

sleep_operator = BashOperator(
    task_id='sleep_task',
    depends_on_past=False,
    bash_command='sleep 5',
    dag=dag)

#-------------------------------------------------------------------------------
# third operator

def print_hello():
    return 'Hello world!'

hello_operator = PythonOperator(
    task_id='hello_task',
    python_callable=print_hello,
    dag=dag)

#-------------------------------------------------------------------------------
# dependencies

sleep_operator.set_upstream(date_operator)
hello_operator.set_upstream(date_operator)
```
该文件创建一个简单的DAG，只有三个运算符，两个BaseOperator(一个打印日期一个休眠5秒)，另一个为PythonOperator在执行任务时调用print_hello函数。

### 3. 测试代码

使用如下命令测试一下我们写的代码的正确性:
```
python ~/opt/airflow/dags/hello_world.py
```
如果你的脚本没有抛出异常，这意味着你代码中没有错误，并且你的Airflow环境是健全的。

下面测试一下我们的DAG中的Task．使用如下命令查看我们`example_hello_world_dag`DAG下有什么Task:
```
xiaosi@yoona:~$ airflow list_tasks example_hello_world_dag
[2017-08-03 11:41:57,097] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-03 11:41:57,220] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-03 11:41:57,241] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
[2017-08-03 11:41:57,490] {models.py:167} INFO - Filling up the DagBag from /home/xiaosi/opt/airflow/dags
date_task
hello_task
sleep_task
```
可以看到我们有三个Task：
```
date_task
hello_task
sleep_task
```
下面分别测试一下这几个Task:

(1) 测试date_task
```
xiaosi@yoona:~$ airflow test example_hello_world_dag date_task 20170803
...
--------------------------------------------------------------------------------
Starting attempt 1 of 2
--------------------------------------------------------------------------------

[2017-08-03 11:44:02,248] {models.py:1342} INFO - Executing <Task(BashOperator): date_task> on 2017-08-03 00:00:00
[2017-08-03 11:44:02,258] {bash_operator.py:71} INFO - tmp dir root location:
/tmp
[2017-08-03 11:44:02,259] {bash_operator.py:80} INFO - Temporary script location :/tmp/airflowtmpxh6da9//tmp/airflowtmpxh6da9/date_tasktQQB0V
[2017-08-03 11:44:02,259] {bash_operator.py:81} INFO - Running command: date
[2017-08-03 11:44:02,264] {bash_operator.py:90} INFO - Output:
[2017-08-03 11:44:02,265] {bash_operator.py:94} INFO - 2017年 08月 03日 星期四 11:44:02 CST
[2017-08-03 11:44:02,266] {bash_operator.py:97} INFO - Command exited with return code 0
```
(2) 测试hello_task
```
xiaosi@yoona:~$ airflow test example_hello_world_dag hello_task 20170803
...
--------------------------------------------------------------------------------
Starting attempt 1 of 2
--------------------------------------------------------------------------------

[2017-08-03 11:45:29,546] {models.py:1342} INFO - Executing <Task(PythonOperator): hello_task> on 2017-08-03 00:00:00
[2017-08-03 11:45:29,551] {python_operator.py:81} INFO - Done. Returned value was: Hello world!
```
(3) 测试sleep_task
```
xiaosi@yoona:~$ airflow test example_hello_world_dag sleep_task 20170803
...
--------------------------------------------------------------------------------
Starting attempt 1 of 2
--------------------------------------------------------------------------------

[2017-08-03 11:46:23,970] {models.py:1342} INFO - Executing <Task(BashOperator): sleep_task> on 2017-08-03 00:00:00
[2017-08-03 11:46:23,981] {bash_operator.py:71} INFO - tmp dir root location:
/tmp
[2017-08-03 11:46:23,983] {bash_operator.py:80} INFO - Temporary script location :/tmp/airflowtmpsuamQx//tmp/airflowtmpsuamQx/sleep_taskuKYlrh
[2017-08-03 11:46:23,983] {bash_operator.py:81} INFO - Running command: sleep 5
[2017-08-03 11:46:23,988] {bash_operator.py:90} INFO - Output:
[2017-08-03 11:46:28,990] {bash_operator.py:97} INFO - Command exited with return code 0
```

如果没有问题，我们就可以运行我们的DAG了．

### 4. 运行DAG

为了运行你的DAG，打开另一个终端，并通过如下命令来启动Airflow调度程序:
```
airflow scheduler
```
**备注**
```
调度程序将发送任务进行执行。默认Airflow设置依赖于一个名为`SequentialExecutor`的执行器，它由调度程序自动启动。在生产中，你可以使用更强大的执行器，如`CeleryExecutor`。
```
当你在浏览器中重新加载Airflow UI时，应该会在Airflow UI中看到你的`hello_world` DAG。

![img](http://img.blog.csdn.net/20170803094344833?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

为了启动DAG Run，首先打开工作流(off键)，然后单击`Trigger Dag`按钮(Links 第一个按钮)，最后单击`Graph View`按钮(Links 第三个按钮)以查看运行进度:

![img](http://img.blog.csdn.net/20170803111755665?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

你可以重新加载图形视图，直到两个任务达到状态成功。完成后，你可以单击hello_task，然后单击`View Log`查看日志。如果一切都按预期工作，日志应该显示一些行，其中之一是这样的：
```
...
[2017-08-03 09:46:43,213] {base_task_runner.py:95} INFO - Subtask: --------------------------------------------------------------------------------
[2017-08-03 09:46:43,213] {base_task_runner.py:95} INFO - Subtask: Starting attempt 1 of 2
[2017-08-03 09:46:43,214] {base_task_runner.py:95} INFO - Subtask: --------------------------------------------------------------------------------
[2017-08-03 09:46:43,214] {base_task_runner.py:95} INFO - Subtask:
[2017-08-03 09:46:43,228] {base_task_runner.py:95} INFO - Subtask: [2017-08-03 09:46:43,228] {models.py:1342} INFO - Executing <Task(PythonOperator): hello_task> on 2017-08-03 09:45:49.070859
[2017-08-03 09:46:43,236] {base_task_runner.py:95} INFO - Subtask: [2017-08-03 09:46:43,235] {python_operator.py:81} INFO - Done. Returned value was: Hello world!
[2017-08-03 09:46:47,378] {jobs.py:2083} INFO - Task exited with return code 0
```
