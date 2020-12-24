
### 1. 特征统计生成

可以通过`facets_overview/python`目录中提供的python代码为数据集创建特征统计协议缓冲区(feature statistics protocol buffer)。数据集可以从tensorflow示例协议缓冲区的TfRecord文件或pandas数据集中分析。

如果要从pandas DataFrame创建proto，请使用`GenericFeatureStatisticsGenerator`类的`ProtoFromDataFrames`方法。 如果要从TfRecord文件创建proto，请使用`FeatureStatisticsGenerator`类的`ProtoFromTfRecordFiles`方法。 这些生成器依赖于numpy和pandas python库。 使用`FeatureStatisticsGenerator`类也需要安装tensorflow。 请参阅这些文件以获取更多文档

Example:
```python
from generic_feature_statistics_generator import GenericFeatureStatisticsGenerator
import pandas as pd
df =  pd.DataFrame({'num' : [1, 2, 3, 4], 'str' : ['a', 'a', 'b', None]}
proto = GenericFeatureStatisticsGenerator().ProtoFromDataFrames([{'name': 'test', 'table': df}])
```

### 2. 可视化

proto使用安装的nbextension可以很容易地在Jupyter Notebook中可视化。proto被加密，然后通过元素上的protoInput属性作为输入提供给facets-overview Polymer web组件。 然后，Web组件显示在Notebook的输出单元中。

Example:
```python
from IPython.core.display import display, HTML
protostr = base64.b64encode(proto.SerializeToString()).decode("utf-8")
HTML_TEMPLATE = """<link rel="import" href="/nbextensions/facets-dist/facets-jupyter.html" >
        <facets-overview id="elem"></facets-overview>
        <script>
          document.querySelector("#elem").protoInput = "{protostr}";
        </script>"""
html = HTML_TEMPLATE.format(protostr=protostr)
display(HTML(html))
```

protoInput属性接受DatasetFeatureStatisticsList协议缓冲区的以下三种形式：
- DatasetFeatureStatisticsList JavaScript类的一个实例，它是由协议缓冲区编译器缓冲区(protocol buffer compiler buffer)创建的类。
- 包含协议缓冲区的序列化二进制的UInt8Array。
- 一个包含base-64编码序列化协议缓冲区的字符串，如上面的代码示例所示。

### 3. 了解可视化

可视化包含两个表：一个用于数字特征，一个用于分类（字符串）特征。 每个表包含该类型的每个特征的行。 这些行包含计算的统计信息和图表，显示数据集中该特征的值的分布。

对于大量数据的数据集，可能存在潜在的统计问题（如特征缺失（无值））以红色和粗体显示。

### 4. 全局控制

可视化的顶部是影响各个表的控件。

`sort-by`下拉菜单可以更改每个表格中特征的排序顺序。 选项有：

- 特征顺序：按照在特征统计模型中的顺序排列
- 不均匀性：按照不均匀的值分配（使用熵）
- 按英文字母顺序
- 缺失/零的个数：根据特征值缺少或包含数字0的数目排序，最大数量为第一个。
- 分配距离（仅在比较多个数据集时可用）：由每个特征的分布形状之间的最大差异（使用卡方形测试）进行排序。

### 5. 图表

图表用来显示表格中的的特征，由图表上方的下拉菜单控制。数字特征的选项有：

- 所有值的直方图，具有10个等宽度的桶
- 所有值的十进制的可视化
- 每个示例的数值的十进制数的可视化
