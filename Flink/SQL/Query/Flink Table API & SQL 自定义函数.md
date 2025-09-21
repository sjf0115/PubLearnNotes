https://github.com/troyyxk/flink_state_cache/blob/4db8b5f2454be2ee4a1e7e5ad425f8f2fa3c890a/flink-simplified-cache-master/docs/content.zh/docs/dev/table/functions/udfs.md


在 Flink Table API 中除了提供大量的内建函数之外，用户也能够实现自定义函数，这样极大地拓展了 Table API 和 SQL 的计算表达能力，使得用户能够更加方便灵活地使用Table API或SQL编写Flink应用。但需要注意的是，自定义函数主要在Table API和SQL中使用，对于DataStream和DataSet API的应用，则无须借助自定义函数实现，只要在相应接口代码中构建计算函数逻辑即可。
通常情况下，用户自定义的函数需要在Flink TableEnvironment中进行注册，然后才能在Table API和SQL中使用。函数注册通过TableEnvironment的registerFunction()方法完成，本质上是将用户自定义好的Function注册到TableEnvironment中的Function CataLog中，每次在调用的过程中直接到CataLog中获取函数信息。Flink目前没有提供持久化注册的接口，因此需要每次在启动应用的时候重新对函数进行注册，且当应用被关闭后，TableEnvironment中已经注册的函数信息将会被清理。
在Table API中，根处理的数据类型以及计算方式的不同将自定义函数一共分为三种类别，分别为Scalar Function、Table Function和Aggregation Function。




## Runtime Integration

有时，用户定义的函数可能需要获取全局运行时信息或在实际工作之前进行一些设置/清理工作。用户自定义函数提供 open() 和 close() 方法，这些方法可以被覆盖，并提供与 DataStream API 的 RichFunction 中的方法类似的功能。

open() 方法在评估方法之前调用一次。 最后一次调用评估方法后的 close() 方法。

open() 方法提供了一个 FunctionContext ，其中包含有关执行用户定义函数的上下文的信息，例如度量组、分布式缓存文件或全局作业参数。

调用 FunctionContext 的对应方法可以得到如下信息：

| 方法 | 描述 |
| :------------- | :------------- |
| getMetricGroup()  | 并行子任务的 Metric Group |
| getCachedFile(name) | 分布式缓存文件的本地临时文件副本 |
| getJobParameter(name, defaultValue) | 与给定 Key 关联的全局作业参数值 |
| getExternalResourceInfos(resourceName) | 返回一组与给定 Key 关联的外部资源信息 |

> 注意：并不是上述所有方法都可以获取，这需要根据执行函数的上下文判断。

以下示例片段显示了如何在标量函数中使用 FunctionContext 来访问全局作业参数：
```jaa

```



https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/dev/table/functions/udfs/#scalar-functions
