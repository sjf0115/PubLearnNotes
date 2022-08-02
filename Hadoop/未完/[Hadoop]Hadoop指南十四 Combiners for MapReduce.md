### 1. 简介

Hadoop Combiner类在MapReduce框架中是一个可选的类，添加在Map类与Reduce类之间，通过汇总Map类的输出数据，从而减少Reduce接收到的数据量（Hadoop Combiner class is an optional class in the MapReduce framework which is added in between the Map class and the Reduce class and is used to reduce the amount of data received by Reduce class by combining the data output from Map）。Combine的主要功能是汇总Map类的输出，以便可以管理来自reducer的数据处理的压力，并可以处理网络拥塞（The main function of a Combiner is to summarize the output from Map class so that the stress of data processing from reducer can be managed and network congestion can be handled.）。由于这个功能，Combiner也被称之为“Mini-Reducer”，“Semi-Reducer”等。

### 2. 工作流程


不同于mapper和reducer，Combiner没有任何预定义的接口。它需要实现reducer接口，并且重写reduce()方法。从技术上讲，Combiner与Reducer有相同的代码。假设我们有一个map类，从记录读取器接收输入，处理后以键值对作为输出（we have a map class which takes an input from the Record Reader and process it to produce key-value pairs as output）。这些键值对中每个单词为key和1作为value，其中1表示key具有的实例数（可以理解为出现个数）。举个例子：
```
<This,1> <is,1> <an,1> <example,1> <This,1> <is,1> <example,1> <This,1> 
```
Combiner处理从Map输出的"key-value"键值对，根据key合并相同的单词，把value转换为一个集合。举个例子：
```
 <This,1,1,1> <is,1,1> <an,1> <example,1,1>
```
This（is，an，example）表示键值对的key，"1，1，1"表示key为"This"的value集合，这里表示单词"This"出现了3次，一共三个1。这之后Reducer处理从Combiner输出的"key-value collection"键值对，并输出最终结果，使<This,1,1,1> 转换为 <This,3>。

### 3. 使用Combiner的MapReduce WordCount例子

WordCount程序是理解MapReduce工作流程的最基本代码。我们将使用WordCount程序来理解Map，Combiner和Reduce类。这个程序包括Map方法，Combine方法和Reduce方法，来计算一个文件中每个单词的出现次数。







