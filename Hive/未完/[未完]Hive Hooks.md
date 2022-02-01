
Hive Hooks
关于数据治理和元数据管理框架，业界有许多开源的系统，比如Apache Atlas，这些开源的软件可以在复杂的场景下满足元数据管理的需求。其实Apache Atlas对于Hive的元数据管理，使用的是 Hive 的 Hooks。需要进行如下配置：

```xml

```

Hooks 是一种事件和消息机制，可以将事件绑定在内部 Hive 的执行流程中，而无需重新编译 Hive。Hook 提供了扩展和继承外部组件的方式。根据不同的 Hook 类型，可以在不同的阶段运行。关于 Hooks 的类型，主要分为以下几种：

## Hooks 类型

### hive.exec.pre.hooks

从名称可以看出，在执行引擎执行查询之前被调用。这个需要在 Hive 对查询计划进行过优化之后才可以使用。使用该 Hooks 需要实现接口：org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext，具体在 hive-site.xml 中的配置如下：
```
<property>
    <name>hive.exec.pre.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### hive.exec.post.hooks

在执行计划执行结束结果返回给用户之前被调用。使用时需要实现接口：org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext，具体在 hive-site.xml 中的配置如下：
```
<property>
    <name>hive.exec.post.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### hive.exec.failure.hooks

在执行计划失败之后被调用。使用时需要实现接口：org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext,具体在 hive-site.xml 中的配置如下：
```
<property>
    <name>hive.exec.failure.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### hive.metastore.init.hooks

HMSHandler 初始化是被调用。使用时需要实现接口：org.apache.hadoop.hive.metastore.MetaStoreInitListener，具体在 hive-site.xml 中的配置如下：
```
<property>
    <name>hive.metastore.init.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### hive.exec.driver.run.hooks

在 Driver.run 开始或结束时运行，使用时需要实现接口：org.apache.hadoop.hive.ql.HiveDriverRunHook，具体在 hive-site.xml 中的配置如下：
```
<property>
    <name>hive.exec.driver.run.hooks</name>
    <value>实现类的全限定名<value/>
</property>
```

### hive.semantic.analyzer.hook

Hive 对查询语句进行语义分析的时候调用。使用时需要集成抽象类：org.apache.hadoop.hive.ql.parse.AbstractSemanticAnalyzerHook，具体在 hive-site.xml 中的配置如下：
```
<property>
    <name>hive.semantic.analyzer.hook</name>
    <value>实现类的全限定名<value/>
</property>
```

| 属性 | 接口(抽象类) |
| :------------- | :------------- |
| hive.exec.pre.hooks | org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext |
| hive.exec.post.hooks | org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext |
| hive.exec.failure.hooks | org.apache.hadoop.hive.ql.hooks.ExecuteWithHookContext |
| hive.metastore.init.hooks | org.apache.hadoop.hive.metastore.MetaStoreInitListener |
| hive.exec.driver.run.hooks | org.apache.hadoop.hive.ql.HiveDriverRunHook |
| hive.semantic.analyzer.hook | org.apache.hadoop.hive.ql.parse.AbstractSemanticAnalyzerHook |


...


- [基于hook机制实现数据血缘系统](https://mp.weixin.qq.com/s/LG2ZWZkV3sFA8sYPcAtEfA)
- https://mp.weixin.qq.com/s/65iKzNfG-x5R13vZ2hI71Q
- https://mp.weixin.qq.com/s/2DadPHe27yrCcnCc2S8oqw
- https://mp.weixin.qq.com/s/ufeZC32bdgdcMo-0WQK7-Q
- https://mp.weixin.qq.com/s/LGK3YPZCe6oPTf48QaAIqA
- https://mp.weixin.qq.com/s/dWdy9hp6SQzcSSeUE5ZSzA
