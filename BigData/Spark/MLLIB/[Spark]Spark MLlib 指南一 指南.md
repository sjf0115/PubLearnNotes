
### 2. 公告:基于DataFrame的API是主要API

备注
```
基于MLLib RDD的API现在扔处于维护状态。
```
从Spark 2.0开始，spark.mllib软件包中基于RDD的API已进入维护模式。 Spark的主要学习API现在是spark.ml包中基于DataFrame的API。

有什么影响？
- MLlib仍将支持spark.MLlib中基于RDD的API，并提供bug修复。
- MLlib不会向基于RDD的API中添加新的功能(features)。
- 在Spark 2.x版本中，MLlib将在基于DataFrames的API中添加新功能，以达到与基于RDD的API的功能相同。
- 达到功能相同（大概估计为Spark 2.3版本）后，将不推荐使用基于RDD的API。
- 预计将在Spark 3.0版本中删除基于RDD的API。

#### 为什么MLlib切换到基于DataFrame的API？

- DataFrames提供比RDD用户体验更加友好的API。DataFrames的许多好处包括Spark Datasources，SQL/DataFrame查询，Tungsten和Catalyst优化以及跨语言的统一API。
- 基于DataFrame的API为MLlib提供了跨ML算法和跨多种语言的统一API。
- DataFrames有助于在实践中使用ML Pipelines，特别是特征变换。有关详细信息，请参[Pipelines指南](http://spark.apache.org/docs/latest/ml-pipeline.html)。

#### 什么是Spark ML？

`Spark ML`不是官方名称，而是偶尔用来指明基于MLlib DataFrame的API。这主要是由于基于DataFrame的API使用的Scala`org.apache.spark.ml`软件包以及我们最初用于强调管道概念的“Spark ML Pipelines”术语。

#### MLlib是否被弃用？

不，MLlib包括基于RDD的API和基于DataFrame的API。基于RDD的API现在处于维护模式。但是，API都不被弃用，也不是MLlib。
