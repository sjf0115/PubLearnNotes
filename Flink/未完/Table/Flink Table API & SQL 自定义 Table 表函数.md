跟标量函数一样，表函数的输入参数也可以是 0 个、1 个或多个标量值;不同的是，它可 以返回任意多行数据。“多行数据”事实上就构成了一个表，所以“表函数”可以认为就是返回一 个表的函数，这是一个“一对多”的转换关系。之前我们介绍过的窗口 TVF，本质上就是表函 数。
类似地，要实现自定义的表函数，需要自定义类来继承抽象类 TableFunction，内部必须 要实现的也是一个名为 eval 的求值方法。与标量函数不同的是，TableFunction 类本身是有一 个泛型参数 T 的，这就是表函数返回数据的类型;而 eval()方法没有返回类型，内部也没有 return 语句，是通过调用 collect()方法来发送想要输出的行数据的。多么熟悉的感觉——回忆一下 DataStream API 中的 FlatMapFunction 和 ProcessFunction，它们的 flatMap 和 processElement 方 法也没有返回值，也是通过 out.collect()来向下游发送数据的。
我们使用表函数，可以对一行数据得到一个表，这和 Hive 中的 UDTF 非常相似。那对于 原先输入的整张表来说，又该得到什么呢?一个简单的想法是，就让输入表中的每一行，与它 转换得到的表进行联结(join)，然后再拼成一个完整的大表，这就相当于对原来的表进行了 扩展。在 Hive 的 SQL 语法中，提供了“侧向视图”(lateral view，也叫横向视图)的功能，可 以将表中的一行数据拆分成多行;Flink SQL 也有类似的功能，是用 LATERAL TABLE 语法来 实现的。
在 SQL 中调用表函数，需要使用 LATERAL TABLE(<TableFunction>)来生成扩展的“侧向 表”，然后与原始表进行联结(Join)。这里的Join操作可以是直接做交叉联结(cross join)， 在 FROM 后用逗号分隔两个表就可以;也可以是以 ON TRUE 为条件的左联结(LEFT JOIN)。


Table Function
和Scalar Function不同，Table Function 将一个或多个标量字段作为输入参数，且经过计算和处理后返回的是任意数量的记录，不再是单独的一个标量指标，且返回结果中可以含有一列或多列指标，根据自定义Table Funciton函数返回值确定，因此从形式上看更像是Table结构数据。

## 2. 定义表函数

定义 Table Function 需要继承 org.apache.flink.table.functions.TableFunction 类，并实现类中的evaluation方法，且所有的自定义函数计算逻辑均在该方法中定义，需要注意方法必须声明为public且名称必须定义为eval。另外在一个TableFunction实现类中可以实现多个evaluation方法，只需要保证参数不相同即可。


在Scala语言Table API中，Table Function可以用在Join、LeftOuterJoin算子中，Table Function相当于产生一张被关联的表，主表中的数据会与Table Function所有产生的数据进行交叉关联。其中LeftOuterJoin算子当Table Function产生结果为空时，Table Function产生的字段会被填为空值。
在应用Table Function之前，需要事先在TableEnvironment中注册Table Function，然后结合LATERAL TABLE关键字使用，根据语句结尾是否增加ON TRUE关键字来区分是Join还是leftOuterJoin操作。如代码清单7-13所示，通过自定义SplitFunction Class继承TableFunction接口，实现根据指定切割符来切分输入字符串，并获取每个字符的长度和HashCode的功能，然后在Table Select操作符和SQL语句中使用定义的SplitFunction。
代码清单7-13 自定义Table Funciton实现将给定字符串切分成多条记录
// 注册输入数据源
tStreamEnv.registerTableSource("InputTable", new InputEventSource)
// 在Scala Table API中使用自定义函数
val split = new SplitFunction(",")
//在join函数中调用Table Function,将string字符串切分成不同的Row,并通过as指定字段名称为str,length,hashcode
table.join(split('origin as('string, 'length, 'hashcode)))
.select('origin, 'str, 'length, 'hashcode)
table.leftOuterJoin(split('origin as('string, 'length, 'hashcode)))
.select('origin, 'str, 'length, 'hashcode)
// 在Table Environment中注册自定义函数,并在SQL中使用
tStreamEnv.registerFunction("split", new SplitFunction(","))
//在SQL中和LATERAL TABLE关键字一起使用Table Function
//和Table API的JOIN一样,产生笛卡儿积结果
tStreamEnv.sqlQuery("SELECT origin, str, length FROM InputTable, LATERAL TABLE(split(origin)) as T(str, length,hashcode)")
//和Table API中的LEFT OUTER JOIN一样,产生左外关联结果
tStreamEnv.sqlQuery("SELECT origin, str, length FROM InputTable, LATERAL TABLE(split(origin)) as T(str, length,hashcode) ON TRUE")
和Scalar Function一样，对于不支持的输出结果类型，可以通过实现TableFunction接口中的getResultType()对输出结果的数据类型进行转换，具体可以参考ScalarFunciton定义。
