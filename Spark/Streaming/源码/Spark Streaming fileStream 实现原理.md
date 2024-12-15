fileStream 是Spark Streaming Basic Source 的一种，用于“近实时”地分析HDFS（或者与HDFS API兼容的文件系统）指定目录（假设：dataDirectory）中新近写入的文件，dataDirectory中的文件需要满足以下约束条件：
- 这些文件格式必须相同，如：统一为文本文件；
- 这些文件在目录dataDirectory中的创建形式比较特殊：必须以原子方式被“移动”或“重命名”至目录dataDirectory中；
- 一旦文件被“移动”或“重命名”至目录dataDirectory中，文件不可以被改变，例如：追加至这些文件的数据可能不会被处理。

之所以称之为“近实时”就是基于约束条件（2），文件的数据必须全部写入完成，并且被“移动”或“重命名”至目录dataDirectory中之后，这些文件才可以被处理。

调用示例如下：
