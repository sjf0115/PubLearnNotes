---
layout: post
author: sjf0115
title: Airflow 使用指南一 安装与启动
date: 2017-12-28 12:55:01
tags:
  - Airflow

categories: Airflow
permalink: how-install-and-startup-airflow
---

### 1. Example

```python
"""
Code that goes along with the Airflow tutorial located at:
https://github.com/airbnb/airflow/blob/master/airflow/example_dags/tutorial.py
"""
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2015, 6, 1),
    'email': ['airflow@airflow.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}

dag = DAG('tutorial', default_args=default_args)

# t1, t2 and t3 are examples of tasks created by instantiating operators
t1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag)

t2 = BashOperator(
    task_id='sleep',
    bash_command='sleep 5',
    retries=3,
    dag=dag)

templated_command = """
    {% for i in range(5) %}
        echo "{{ ds }}"
        echo "{{ macros.ds_add(ds, 7)}}"
        echo "{{ params.my_param }}"
    {% endfor %}
"""

t3 = BashOperator(
    task_id='templated',
    bash_command=templated_command,
    params={'my_param': 'Parameter I passed in'},
    dag=dag)

t2.set_upstream(t1)
t3.set_upstream(t1)
```

你需要搞清楚的是（对于刚上手的人来说可能不是很直观），这个Airflow Python脚本只是一个配置文件，使用代码的方式指定了DAG的结构(与oozie使用xml方式不同)。这里定义的实际任务将在与此脚本的上下文不同的上下文中运行。不同的任务在不同的时间点在不同的工作节点(worker)上运行，这意味着这个脚本不能进行跨任务之间的交流。为此，我们有一个更高级的功能，称为`XCom`。

有人可能会将DAG定义文件认为是可以进行一些实际数据处理的地方 - 根本不是这样！ 脚本的目的是定义一个DAG对象。它需要快速评估（秒级别，而不是分钟级别），因为调度程序将定期执行它以反映更改（如果有的话）。

### 2. 导入模块

Airflow管道只是一个Python脚本，目的是定义一个Airflow DAG对象。我们从导入我们需要的类库开始。

```python
# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

# Operators; we need this to operate!
from airflow.operators.bash_operator import BashOperator
```

### 3. 默认参数

我们将要创建一个DAG和一些任务，我们可以选择将一组参数传递给每个任务的构造函数（这将变得多余），或者（更好的）我们可以定义一个默认参数的字典，可以在创建任务时使用。

```python
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2015, 6, 1),
    'email': ['airflow@airflow.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}
```
有关BaseOperator参数及它们是干什么的的更多信息，请参阅:`airflow.models.BaseOperator`文档。

另外，请注意，可以定义不同的参数集，用于不同的目的。一个例子就是在生产和开发环境之间设置不同的设置，使用不同的参数集。

### 4. 实例化DAG

我们需要一个DAG对象来嵌套我们的任务。这里我们传递一个定义`dag_id`的字符串(tutorial)，它用作DAG的唯一标识符。我们还传递我们刚刚定义的默认参数字典，并为DAG的schedule_interval参数设置为1天。

```
dag = DAG(
    'tutorial', default_args=default_args, schedule_interval=timedelta(1))
```
### 5. 任务(Tasks)

当实例化operator对象时会生成任务。从一个operator中实例化的任意对象都称为构造器。第一个参数`task_id`作为该任务的唯一标识符。

```python
t1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag)

t2 = BashOperator(
    task_id='sleep',
    bash_command='sleep 5',
    retries=3,
    dag=dag)
```

注意我们如何把operator特定参数(bash_command)和从BaseOperator继承来的对所有operator都常用的公共参数(retries)组成的混合参数传递到operator的构造器中的。另外，请注意，在第二个任务中，我们用参数3覆盖`retries`参数。

任务参数的优先规则如下：
- 显示传递的参数
- `default_args`字典中存在的值
- operator的默认值(如果存在)

### 6. Jinja模板

Airflow充分利用了`Jinja 模板`，为管道作者提供了一套内置的参数和宏。Airflow还为管道作者提供了钩子(hooks)来定义自己的参数，宏和模板。

本教程几乎无法在Airflow中对模板进行操作，但本节的目标是让你了解此功能的存在，让你熟悉一下双大括号，并认识一下最常见的模板变量:`{{ ds }}`。

```python
templated_command = """
    {% for i in range(5) %}
        echo "{{ ds }}"
        echo "{{ macros.ds_add(ds, 7) }}"
        echo "{{ params.my_param }}"
    {% endfor %}
"""

t3 = BashOperator(
    task_id='templated',
    bash_command=templated_command,
    params={'my_param': 'Parameter I passed in'},
    dag=dag)
```

请注意，`templated_command`在`{％％}`块中包含代码逻辑，可以像`{{ds}}`一样引用参数，像`{{macros.ds_add（ds，7）}}`中一样调用函数，并在`{{params.my_param}}`引用自定义参数。

文件也可以传递给`bash_command`参数，如`bash_command ='templated_command.sh'`，文件位置是相对于包含管道文件(在这个例子中为tutorial.py)的目录。这由于许多原因而需要的，例如分离脚本的逻辑和流水线代码，允许在不同语言组成的文件中进行适当的代码突出显示。

### 7. 建立依赖关系

我们有两个不相互依赖的简单任务。 这里有几种方法可以定义它们之间的依赖关系：
```python
t2.set_upstream(t1)

# This means that t2 will depend on t1
# running successfully to run
# It is equivalent to
# t1.set_downstream(t2)

t3.set_upstream(t1)

# all of this is equivalent to
# dag.set_dependency('print_date', 'sleep')
# dag.set_dependency('print_date', 'templated')
```
请注意，当执行脚本时，如果在DAG中找到一条环形链路(例如A依赖于B，B又依赖于C，C又依赖于A)或者一个依赖被多次引用时引发异常(when it finds cycles in your DAG or when a dependency is referenced more than once)。

### 8. 概括

经上述介绍之后，我们有了一个基本的DAG。此时我们的代码应该如下所示：
```python
"""
Code that goes along with the Airflow located at:
http://airflow.readthedocs.org/en/latest/tutorial.html
"""
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2015, 6, 1),
    'email': ['airflow@airflow.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}

dag = DAG(
    'tutorial', default_args=default_args, schedule_interval=timedelta(1))

# t1, t2 and t3 are examples of tasks created by instantiating operators
t1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag)

t2 = BashOperator(
    task_id='sleep',
    bash_command='sleep 5',
    retries=3,
    dag=dag)

templated_command = """
    {% for i in range(5) %}
        echo "{{ ds }}"
        echo "{{ macros.ds_add(ds, 7)}}"
        echo "{{ params.my_param }}"
    {% endfor %}
"""

t3 = BashOperator(
    task_id='templated',
    bash_command=templated_command,
    params={'my_param': 'Parameter I passed in'},
    dag=dag)

t2.set_upstream(t1)
t3.set_upstream(t1)
```
### 9. 测试

#### 9.1 运行脚本

是时候运行一些测试样例了。首先让我们确定管道解析。假设我们正在将上一步`tutorial.py`中的代码保存在`workflow.cfg`中配置(dags_folder)的DAG文件夹中。DAG的默认存储位置为`$AIRFLOW_HOME/dags`中。
```
python ~/airflow/dags/tutorial.py
```
如果你的脚本没有抛出异常，这意味着你代码中没有可怕的错误，并且你的Airflow环境是健全的。

#### 9.2 命令行元数据验证

我们来运行一些命令来进一步验证这个脚本。
```
# print the list of active DAGs
airflow list_dags

# prints the list of tasks the "tutorial" dag_id
airflow list_tasks tutorial

# prints the hierarchy of tasks in the tutorial DAG
airflow list_tasks tutorial --tree
```
验证结果:
```
xiaosi@yoona:~$ airflow list_dags
[2017-08-02 21:35:06,134] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 21:35:06,274] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 21:35:06,293] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
[2017-08-02 21:35:06,607] {models.py:167} INFO - Filling up the DagBag from /home/xiaosi/opt/airflow/dags


-------------------------------------------------------------------
DAGS
-------------------------------------------------------------------
example_bash_operator
example_branch_dop_operator_v3
example_branch_operator
example_http_operator
example_passing_params_via_test_command
example_python_operator
example_short_circuit_operator
example_skip_dag
example_subdag_operator
example_subdag_operator.section-1
example_subdag_operator.section-2
example_trigger_controller_dag
example_trigger_target_dag
example_xcom
latest_only
latest_only_with_trigger
test_utils
tutorial

xiaosi@yoona:~$ airflow list_tasks tutorial
[2017-08-02 21:35:37,444] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 21:35:37,550] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 21:35:37,569] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
[2017-08-02 21:35:37,811] {models.py:167} INFO - Filling up the DagBag from /home/xiaosi/opt/airflow/dags
print_date
sleep
templated
xiaosi@yoona:~$ airflow list_tasks tutorial --tree
[2017-08-02 21:35:46,470] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 21:35:46,578] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 21:35:46,597] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
[2017-08-02 21:35:46,841] {models.py:167} INFO - Filling up the DagBag from /home/xiaosi/opt/airflow/dags
<Task(BashOperator): sleep>
    <Task(BashOperator): print_date>
<Task(BashOperator): templated>
    <Task(BashOperator): print_date>
```
#### 9.3 测试

我们通过在特定日期运行实际的任务实例进行测试。在此上下文中指定的日期是一个`execution_date`，它模拟在特定日期+时间上运行任务或dag的调度程序：
```
# command layout: command subcommand dag_id task_id date

# testing print_date
airflow test tutorial print_date 2015-06-01

# testing sleep
airflow test tutorial sleep 2015-06-01
```
运行结果:
```
xiaosi@yoona:~$ airflow test tutorial print_date 2015-06-01
[2017-08-02 21:39:55,781] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 21:39:55,889] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 21:39:55,908] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
[2017-08-02 21:39:56,153] {models.py:167} INFO - Filling up the DagBag from /home/xiaosi/opt/airflow/dags
[2017-08-02 21:39:56,315] {models.py:1126} INFO - Dependencies all met for <TaskInstance: tutorial.print_date 2015-06-01 00:00:00 [None]>
[2017-08-02 21:39:56,317] {models.py:1126} INFO - Dependencies all met for <TaskInstance: tutorial.print_date 2015-06-01 00:00:00 [None]>
[2017-08-02 21:39:56,317] {models.py:1318} INFO -
--------------------------------------------------------------------------------
Starting attempt 1 of 2
--------------------------------------------------------------------------------

[2017-08-02 21:39:56,318] {models.py:1342} INFO - Executing <Task(BashOperator): print_date> on 2015-06-01 00:00:00
[2017-08-02 21:39:56,327] {bash_operator.py:71} INFO - tmp dir root location:
/tmp
[2017-08-02 21:39:56,328] {bash_operator.py:80} INFO - Temporary script location :/tmp/airflowtmpc1BGXE//tmp/airflowtmpc1BGXE/print_dateITSGQK
[2017-08-02 21:39:56,328] {bash_operator.py:81} INFO - Running command: date
[2017-08-02 21:39:56,332] {bash_operator.py:90} INFO - Output:
[2017-08-02 21:39:56,335] {bash_operator.py:94} INFO - 2017年 08月 02日 星期三 21:39:56 CST
[2017-08-02 21:39:56,336] {bash_operator.py:97} INFO - Command exited with return code 0
xiaosi@yoona:~$
xiaosi@yoona:~$
xiaosi@yoona:~$ airflow test tutorial sleep 2015-06-01
[2017-08-02 21:40:41,594] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 21:40:41,700] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 21:40:41,719] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
[2017-08-02 21:40:41,964] {models.py:167} INFO - Filling up the DagBag from /home/xiaosi/opt/airflow/dags
[2017-08-02 21:40:42,126] {models.py:1126} INFO - Dependencies all met for <TaskInstance: tutorial.sleep 2015-06-01 00:00:00 [None]>
[2017-08-02 21:40:42,128] {models.py:1126} INFO - Dependencies all met for <TaskInstance: tutorial.sleep 2015-06-01 00:00:00 [None]>
[2017-08-02 21:40:42,128] {models.py:1318} INFO -
--------------------------------------------------------------------------------
Starting attempt 1 of 2
--------------------------------------------------------------------------------

[2017-08-02 21:40:42,128] {models.py:1342} INFO - Executing <Task(BashOperator): sleep> on 2015-06-01 00:00:00
[2017-08-02 21:40:42,137] {bash_operator.py:71} INFO - tmp dir root location:
/tmp
[2017-08-02 21:40:42,138] {bash_operator.py:80} INFO - Temporary script location :/tmp/airflowtmpfLOkuA//tmp/airflowtmpfLOkuA/sleepOoXZ0X
[2017-08-02 21:40:42,138] {bash_operator.py:81} INFO - Running command: sleep 5
[2017-08-02 21:40:42,143] {bash_operator.py:90} INFO - Output:
[2017-08-02 21:40:47,146] {bash_operator.py:97} INFO - Command exited with return code 0
```
现在是否还记得我们之前用模板做了什么？ 通过运行以下命令，查看如何渲染和执行此模板：
```
# testing templated
airflow test tutorial templated 2015-06-01
```
运行结果:
```
xiaosi@yoona:~$ airflow test tutorial templated 2015-06-01
[2017-08-02 21:43:40,089] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 21:43:40,196] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 21:43:40,214] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
[2017-08-02 21:43:40,458] {models.py:167} INFO - Filling up the DagBag from /home/xiaosi/opt/airflow/dags
[2017-08-02 21:43:40,620] {models.py:1126} INFO - Dependencies all met for <TaskInstance: tutorial.templated 2015-06-01 00:00:00 [None]>
[2017-08-02 21:43:40,622] {models.py:1126} INFO - Dependencies all met for <TaskInstance: tutorial.templated 2015-06-01 00:00:00 [None]>
[2017-08-02 21:43:40,622] {models.py:1318} INFO -
--------------------------------------------------------------------------------
Starting attempt 1 of 2
--------------------------------------------------------------------------------

[2017-08-02 21:43:40,623] {models.py:1342} INFO - Executing <Task(BashOperator): templated> on 2015-06-01 00:00:00
[2017-08-02 21:43:40,638] {bash_operator.py:71} INFO - tmp dir root location:
/tmp
[2017-08-02 21:43:40,639] {bash_operator.py:80} INFO - Temporary script location :/tmp/airflowtmpHmgW9g//tmp/airflowtmpHmgW9g/templated086SvH
[2017-08-02 21:43:40,639] {bash_operator.py:81} INFO - Running command:

    echo "2015-06-01"
    echo "2015-06-08"
    echo "Parameter I passed in"

    echo "2015-06-01"
    echo "2015-06-08"
    echo "Parameter I passed in"

    echo "2015-06-01"
    echo "2015-06-08"
    echo "Parameter I passed in"

    echo "2015-06-01"
    echo "2015-06-08"
    echo "Parameter I passed in"

    echo "2015-06-01"
    echo "2015-06-08"
    echo "Parameter I passed in"

[2017-08-02 21:43:40,643] {bash_operator.py:90} INFO - Output:
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - 2015-06-01
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - 2015-06-08
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - Parameter I passed in
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - 2015-06-01
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - 2015-06-08
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - Parameter I passed in
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - 2015-06-01
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - 2015-06-08
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - Parameter I passed in
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - 2015-06-01
[2017-08-02 21:43:40,644] {bash_operator.py:94} INFO - 2015-06-08
[2017-08-02 21:43:40,645] {bash_operator.py:94} INFO - Parameter I passed in
[2017-08-02 21:43:40,645] {bash_operator.py:94} INFO - 2015-06-01
[2017-08-02 21:43:40,645] {bash_operator.py:94} INFO - 2015-06-08
[2017-08-02 21:43:40,645] {bash_operator.py:94} INFO - Parameter I passed in
[2017-08-02 21:43:40,645] {bash_operator.py:97} INFO - Command exited with return code 0
```
这将显示事件的详细日志，并最终运行你的bash命令并打印结果。

请注意，`airflow test`命令在本地运行任务实例，将其日志输出到stdout（屏幕上），不会影响依赖关系，并且不会将状态（运行，成功，失败，...）发送到数据库。 它只是允许简单的测试单个任务实例。

#### 9.4 Backfill

一切看起来都运行正常，所以让我们运行一个backfill。`backfill`将遵照依赖关系，并将日志发送到文件中，与数据库通信以记录状态。如果你启动webserver，你可以跟踪进度。如果你有兴趣可以在backfill过程中跟踪进度，`airflow webserver`将启动Web服务器。

注意，如果使用`depends_on_past = True`，则单个任务实例将取决于上一个任务实例的成功与否，如果指定本身的start_date，则忽略此依赖关系(except for the start_date specified itself, for which this dependency is disregarded.)。

此上下文中的日期范围是`start_date`和可选的`end_date`，用于使用此dag中的任务实例填充运行计划。
```python
# optional, start a web server in debug mode in the background
# airflow webserver --debug &

# start your backfill on a date range
airflow backfill tutorial -s 2015-06-01 -e 2015-06-07
```

原文:http://airflow.incubator.apache.org/tutorial.html#example-pipeline-definition
