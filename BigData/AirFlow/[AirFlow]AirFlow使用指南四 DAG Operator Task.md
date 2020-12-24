### 1. DAG

在Airflow中，DAG或有向无环图是你运行所有任务的集合，以某种组织方式来反映所有任务之间的关系和依赖。

例如，一个简单的DAG可以包括三个任务：A，B和C.可以说A必须在B运行之前成功运行，但C可以随时运行。 可以说任务A在5分钟后超时，为防止失败，B可以最多重启5次。也可以说工作流从某个特定日期开始每晚10点运行。

以这种方式，DAG描述了你如何执行工作流程; 但是请注意，我们还没有说出我们实际想要做的事情！ A，B和C可以是任何东西。也许在C发送电子邮件时，A为B准备数据以进行分析。或者A监视你的位置，以便B可以打开你的车库门，而C打开房子的灯。重要的是，DAG不关心其内部任务干了什么;它的目的是确保在正确的时间或以正确的顺序干任何事情，或可以正确处理任何意想不到的问题。

DAG在标准的Python文件中定义，放置在Airflow的`DAG_FOLDER`中。Airflow将执行每个文件中的代码来动态构建DAG对象。你可以拥有任意数量的DAG，每个可以拥有任意数量的任务。通常，每一个应该对应于一个逻辑工作流。

#### 1.1 作用域(scope)

Airflow将加载从DAG文件导入的任何DAG对象。最重要的是，这意味着DAG必须出现在`globals()`中。考虑以下两个DAG。只有`dag_1`将被加载;另一个只出现在局部作用域内。
```
dag_1 = DAG('this_dag_will_be_discovered')

def my_function()
    dag_2 = DAG('but_this_dag_will_not')

my_function()
```

有时这有很好的用处。例如，`SubDagOperator`的通用模式是在函数内定义子dag，以便Airflow不会将其作为独立DAG进行加载。

#### 1.2 默认参数

如果将`default_args`字典传递给DAG，DAG将会将字典应用于其内部的任何Operator上。这很容易的将常用参数应用于多个Operator，而无需多次键入。

```
default_args=dict(
    start_date=datetime(2016, 1, 1),
    owner='Airflow')

dag = DAG('my_dag', default_args=default_args)
op = DummyOperator(task_id='dummy', dag=dag)
print(op.owner) # Airflow
```
#### 1.3 上下文管理器(Context Manager)

**备注**
```
Airflow 1.8引入
```
DAG可用作上下文管理器，以自动为DAG分配新的Operator。

```
with DAG('my_dag', start_date=datetime(2016, 1, 1)) as dag:
    op = DummyOperator('op')

op.dag is dag # True
```

### 2. Operators

DAG描述了如何运行工作流，`Operators`决定了实际如何完成。

Operator描述了工作流中的单个任务。Operator通常（但不总是）原子性的，这意味着它们可以独立存在，不需要与其他Operator共享资源。DAG将确保Operator按正确的顺序运行; 除了这些依赖之外，Operator通常独立运行。实际上，他们可能会运行在两台完全不同的机器上。

这是一个微小但非常重要的一点:一般来说，如果两个Operator需要共享信息，如文件名或少量数据，则应考虑将它们组合成一个Operator。如果绝对不可避免，Airflow确实有一个名为`XCom`的Operator可以交叉通信。

Airflow为Operator提供许多常见任务，包括：
- `BashOperator` - 执行bash命令
- `PythonOperator` - 调用任意的Python函数
- `EmailOperator` - 发送邮件
- `HTTPOperator` - 发送 HTTP 请求
- `SqlOperator` - 执行 SQL 命令
- `Sensor` - 等待一定时间，文件，数据库行，S3键等...

除了这些基本的构建块之外，还有更多的特定Operator:`DockerOperator`，`HiveOperator`，`S3FileTransferOperator`，`PrestoToMysqlOperator`，`SlackOperator` ...总之你能想到的！

`airflow/contrib/`目录包含更多由社区建立的Operator。这些Operator并不总是与主包(in the main distribution)中的Operator一样完整或经过很好的测试，但允许用户更轻松地向平台添加新功能。

Operators只有在分配给DAG时，才会被Airflow加载。

#### 2.1 DAG分配

**备注**
```
在Airflow 1.8版本中引入
```
Operator不需要立即分配给DAG（以前dag是必需的参数）。但是一旦operator分配给DAG, 它就不能transferred或者unassigned. 当一个Operator创建时，通过延迟分配或甚至从其他Operator推断，可以让DAG得到明确的分配(DAG assignment can be done explicitly when the operator is created, through deferred assignment, or even inferred from other operators.)．

```python
dag = DAG('my_dag', start_date=datetime(2016, 1, 1))

# 明确指定DAG
explicit_op = DummyOperator(task_id='op1', dag=dag)

# 延迟分配
deferred_op = DummyOperator(task_id='op2')
deferred_op.dag = dag

# 从其他Operator推断 (linked operators must be in the same DAG)
inferred_op = DummyOperator(task_id='op3')
inferred_op.set_upstream(deferred_op)
```
#### 2.2 位移组合

**备注**
```
在Airflow 1.8版本中引入
```
传统上，使用`set_upstream()`和`set_downstream()`方法来设置Operator之间的依赖关系。在Airflow 1.8中，可以使用Python位移操作符`>>`和`<<`。 以下四个语句在功能上相当：
```python
op1 >> op2
op1.set_downstream(op2)

op2 << op1
op2.set_upstream(op1)
```
当使用位移操作符去设置Operator依赖关系时，根据位移操作符指向的方向来判断Operator之间的依赖关系。例如，`op1 >> op2` 表示op1先运行，op2然后运行。可以组合多个Operator - 记住从左到右执行的链，总是返回最右边的对象。 例如：
```
op1 >> op2 >> op3 << op4
```
等价于:
```
op1.set_downstream(op2)
op2.set_downstream(op3)
op3.set_upstream(op4)
```
为方便起见，位移操作符也可以与DAG一起使用。 例如:
```
dag >> op1 >> op2
```
等价于:
```
op1.dag = dag
op1.set_downstream(op2)
```
我们可以把这一切整合在一起，建立一个简单的管道:
```
with DAG('my_dag', start_date=datetime(2016, 1, 1)) as dag:
    (
        dag
        >> DummyOperator(task_id='dummy_1')
        >> BashOperator(
            task_id='bash_1',
            bash_command='echo "HELLO!"')
        >> PythonOperator(
            task_id='python_1',
            python_callable=lambda: print("GOODBYE!"))
    )
```

### 3. Task

一旦Operator被实例化，它被称为"任务"。实例化为在调用抽象Operator时定义一些特定值，参数化任务使之成为DAG中的一个节点。

### 4. 任务实例化

一个任务实例表示任务的一次特定运行，并且被表征为dag，任务和时间点的组合。任务实例也有指示性状态，可能是“运行”，“成功”，“失败”，“跳过”，“重试”等。

### 5. 工作流

现在你已经熟悉了Airflow的核心构建块。一些概念可能听起来似曾相似，但词汇可以这样概念化：

- DAG：描述工作发生的顺序
- Operator：执行某些工作的模板类
- Task：Operator的参数化实例
- TaskInstances(任务实例)：1）已分配给DAG的任务，2）具有DAG特定运行相关的状态

通过组合`DAG`和`Operators`来创建`TaskInstances`，可以构建复杂的工作流。


原文:http://airflow.incubator.apache.org/concepts.html#
