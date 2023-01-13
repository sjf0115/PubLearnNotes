
> Hive 版本：2.3.4

## 1. Hive Hooks

业界有许多开源的数据治理和元数据管理框架，可以在复杂的场景下满足元数据管理的需求。其中比较出名的 Apache Atlas 就是利用 Hive 的 Hooks 实现 Hive  的元数据管理。Hooks 是一种事件和消息机制，与插件机制比较类似，可以将事件绑定在 Hive 的执行流程中，而无需重新编译 Hive。根据不同的 Hook 类型，可以在不同的阶段触发运行。

## 2. Hooks 类型

下面关于 Hooks 的类型，主要分为以下几种：

### 2.1 hive.exec.driver.run.hooks

在 Driver.run 开始或结束时运行。使用时需要实现 `org.apache.hadoop.hive.ql.HiveDriverRunHook` 接口：
```java
public interface HiveDriverRunHook extends Hook {
  public void preDriverRun(HiveDriverRunHookContext hookContext) throws Exception;
  public void postDriverRun(HiveDriverRunHookContext hookContext) throws Exception;
}
```
具体在 hive-site.xml 中的配置如下：
```xml
<property>
    <name>hive.exec.driver.run.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### 2.2 hive.semantic.analyzer.hook

Hive 对查询语句进行语义分析的时候调用。使用时需要实现接口：`org.apache.hadoop.hive.ql.parse.HiveSemanticAnalyzerHook`：
```java
public interface HiveSemanticAnalyzerHook extends Hook {
  public ASTNode preAnalyze(HiveSemanticAnalyzerHookContext context, ASTNode ast) throws SemanticException;
  public void postAnalyze(HiveSemanticAnalyzerHookContext context, List<Task<? extends Serializable>> rootTasks) throws SemanticException;
}
```
也可以使用抽象类：`org.apache.hadoop.hive.ql.parse.AbstractSemanticAnalyzerHook`：
```java
public abstract class AbstractSemanticAnalyzerHook implements HiveSemanticAnalyzerHook {
  public ASTNode preAnalyze(HiveSemanticAnalyzerHookContext context,ASTNode ast) throws SemanticException {
    return ast;
  }
  public void postAnalyze(HiveSemanticAnalyzerHookContext context, List<Task<? extends Serializable>> rootTasks) throws SemanticException {
  }
}
```

具体在 hive-site.xml 中的配置如下：
```xml
<property>
    <name>hive.semantic.analyzer.hook</name>
    <value>实现类的全限定名<value/>
</property>
```

### 2.3 hive.exec.query.redactor.hooks

在语法分析之后，生成 QueryPlan 之前时调用。所以执行它的时候语法分析已完成，具体要跑的任务已定，目的在于完成 QueryString 的替换，比如 QueryString 中包含敏感的表或字段信息，在这里都可以完成替换，从而在 Yarn 的 RM 界面或其他方式查询该任务的时候，会显示经过替换后的 HQL。使用时需要继承抽象类：`org.apache.hadoop.hive.ql.hooks.Redactor`：
```java
public abstract class Redactor implements Hook, Configurable {
  private Configuration conf;
  public void setConf(Configuration conf) {
    this.conf = conf;
  }

  public Configuration getConf() {
    return conf;
  }
  public String redactQuery(String query) {
    return query;
  }
}
```
具体在 hive-site.xml 中的配置如下：
```xml
<property>
    <name>hive.exec.query.redactor.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### 2.4 hive.exec.pre.hooks

从名称可以看出，在执行引擎执行查询之前被调用。在执行计划 QueryPlan 生成完并通过鉴权后，就会执行具体的 Task，而 Task 执行之前就是调用该 Hook。该 Hook 的实现方式有两种，一是实现 `org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext` 接口：
```java
public interface ExecuteWithHookContext extends Hook {
  void run(HookContext hookContext) throws Exception;
}
```
另一种是实现 `org.apache.hadoop.hive.ql.hooks.PreExecute` 接口，不过该接口中的方法已经标记为 `@Deprecated`，不在建议使用：
```java
public interface PreExecute extends Hook {
  @Deprecated
  public void run(SessionState sess, Set<ReadEntity> inputs,
      Set<WriteEntity> outputs, UserGroupInformation ugi)
    throws Exception;
}
```
具体在 hive-site.xml 中的配置如下：
```xml
<property>
    <name>hive.exec.pre.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### 2.5 hive.exec.post.hooks

在执行计划 QueryPlan 生成完并通过鉴权后，就会执行具体的 Task，而 Task 执行之后就是调用该 Hook。该 Hook 的实现方式跟 `hive.exec.pre.hooks` 类似，一是实现 `org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext` 接口：
```java
public interface ExecuteWithHookContext extends Hook {
  void run(HookContext hookContext) throws Exception;
}
```
另一种是实现 `org.apache.hadoop.hive.ql.hooks.PostExecute` 接口，不过该接口中的方法已经标记为 `@Deprecated`，不在建议使用：
```java
public interface PostExecute extends Hook {
  @Deprecated
  void run(SessionState sess, Set<ReadEntity> inputs,
      Set<WriteEntity> outputs, LineageInfo lInfo,
      UserGroupInformation ugi) throws Exception;
}
```
具体在 hive-site.xml 中的配置如下：
```xml
<property>
    <name>hive.exec.post.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### 2.6 hive.exec.failure.hooks

在执行计划失败之后被调用。使用时需要实现 `org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext` 接口：
```java
public interface ExecuteWithHookContext extends Hook {
  void run(HookContext hookContext) throws Exception;
}
```
具体在 hive-site.xml 中的配置如下：
```xml
<property>
    <name>hive.exec.failure.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

## 3. 说明

通过上面可以知道通过 `org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext` 接口可以实现在三种场景下调用：
- 在 Task 执行之前调用，对应 HookType.PRE_EXEC_HOOK 类型；通过 hive.exec.pre.hooks 属性进行设置；
- 在 Task 执行失败时调用，对应 HookType.ON_FAILURE_HOOK 类型；通过 hive.exec.failure.hooks 属性进行设置；
- 在 Task 执行之后调用，对应 HookType.POST_EXEC_HOOK 类型；通过 hive.exec.post.hooks 属性进行设置；

## 4. 实战

### 4.1 依赖

如果开发自定义的 Hook，需要添加如下依赖：
```xml
<dependency>
    <groupId>org.apache.hive</groupId>
    <artifactId>hive-jdbc</artifactId>
    <version>${hive.version}</version>
    <scope>provided</scope>
</dependency>
```

### 4.2 开发自定义 Hook

我们以在 Task 执行之后调用 Hook 为例进行说明。上面已经讲过该 Hook 的实现方式有两种：一是实现 `org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext` 接口：
```java
public class PostExecuteWithHookContextHook implements ExecuteWithHookContext {
    private static final Logger LOG = LoggerFactory.getLogger(PostExecuteWithHookContextHook.class);
    @Override
    public void run(HookContext context) throws Exception {
        HookContext.HookType hookType = context.getHookType();
        // Task 执行之后调用
        if (!Objects.equals(hookType, HookContext.HookType.POST_EXEC_HOOK)) {
            return;
        }
        // 执行计划
        QueryPlan plan = context.getQueryPlan();
        // 操作名称
        String operationName = plan.getOperationName();
        // 查询
        String query = plan.getQueryString();

        LOG.info("OperationName: {}", operationName);
        LOG.info("Query: {}", query);
    }
}
```
> 完整代码实现：[PostExecuteWithHookContextHook](https://github.com/sjf0115/data-example/blob/master/hive-example/src/main/java/com/hive/example/hook/PostExecuteWithHookContextHook.java)

另一种是实现 `org.apache.hadoop.hive.ql.hooks.PostExecute` 接口，不过该接口中的方法已经标记为 `@Deprecated`，不在建议使用：
```java
public class PostExecuteHook implements PostExecute {
    private static final Logger LOG = LoggerFactory.getLogger(PostExecuteHook.class);
    @Override
    public void run(SessionState ss, Set<ReadEntity> inputs, Set<WriteEntity> outputs, LineageInfo lInfo, UserGroupInformation ugi) throws Exception {
        LOG.info("Command: {}", ss.getLastCommand());
    }
}
```
> 完整代码实现：[PostExecuteWithHookContextHook](https://github.com/sjf0115/data-example/blob/master/hive-example/src/main/java/com/hive/example/hook/PostExecuteHook.java)

### 4.3 配置

首先将上述代码编译成 jar 包，放在 $HIVE_HOME/lib 目录下，或者使用在 Hive 的客户端中执行添加 jar 包的命令：
```
add jar hive-example-1.0.jar;
```
为了能让 Hive 知道我们定义了两个自定义 Hook，并希望在 Task 执行之后调用，所以需要在 Hive-site.xml 文件中配置 `hive.exec.post.hooks` 对应的属性值：
```xml
<property>
  <name>hive.exec.post.hooks</name>
  <value>com.hive.example.hook.PostExecuteWithHookContextHook,com.hive.example.hook.PostExecuteHook</value>
</property>
```
为了方便，我们也可以直接使用客户端命令进行配置：
```
set hive.exec.post.hooks=com.hive.example.hook.PostExecuteWithHookContextHook,com.hive.example.hook.PostExecuteHook;
```
> 配置的类名为实现 Hook 类的全限定名

### 4.4 测试

在自定义 Hook 中我们对一些操作进行了监控，当监控到这些操作时会触发一些自定义的代码(比如输出日志)。当我们在 Hive CLI 中输入如下查询命令：
```sql
SELECT COUNT(*) FROM behavior;
```
在 `$HIVE_HOME/logs/hive.log` 日志文件可以看到如下监控日志输出：
```java
2022-12-29T22:36:42,876  INFO [53111db5-b1d7-4168-bc09-e3a5f74edb60 main] hook.PostExecuteWithHookContextHook: OperationName: QUERY
2022-12-29T22:36:42,876  INFO [53111db5-b1d7-4168-bc09-e3a5f74edb60 main] hook.PostExecuteWithHookContextHook: Query: SELECT COUNT(*) FROM behavior
2022-12-29T22:36:42,877  INFO [53111db5-b1d7-4168-bc09-e3a5f74edb60 main] hook.PostExecuteHook: Command: SELECT COUNT(*) FROM behavior
```
当我们在 Hive CLI 中输入 `SHOW TABLES` 命令时，输出如下监控日志：

```java
2022-12-29T23:00:37,147  INFO [53111db5-b1d7-4168-bc09-e3a5f74edb60 main] hook.PostExecuteWithHookContextHook: OperationName: SHOWTABLES
2022-12-29T23:00:37,147  INFO [53111db5-b1d7-4168-bc09-e3a5f74edb60 main] hook.PostExecuteWithHookContextHook: Query: SHOW TABLES
2022-12-29T23:00:37,147  INFO [53111db5-b1d7-4168-bc09-e3a5f74edb60 main] hook.PostExecuteHook: Command: SHOW TABLES
```
