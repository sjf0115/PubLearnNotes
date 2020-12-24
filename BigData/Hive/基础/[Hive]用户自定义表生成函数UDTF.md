### 1. 简介

尽管UDF可以返回array（数组）和structure（结构体），但是它们不能返回多列或多行。用户自定义表生成函数UDTF通过一个可以返回多列甚至多行的程序接口来满足这个需求。

Hive中常见的内置表生成函数，包括`explode()`，`json_tuple()`和`inline()`。

在这篇文章中，我们利用`org.apache.hadoop.hive.ql.udf.generic.GenericUDTF`接口，看看用户自定义表生成函数。

### 2. 可以产生多行数据的UDTF

Hive中有一个内置表生成函数`exploe()`，`explode()`方法的输入是一个数组，而将数组中的每个元素都作为一行输出。达到相同效果的另一种可选方式是使用UDTF，基于某个输入产生多行输出。这里我们展示一个UDTF，将json格式的数据的每一个字段作为一行进行输出。

#### 2.1 演示数据

下面提供了一份演示数据，包括两列数据，第一列是用户名称，第二列是火车票涉及的几个费用（车票费，服务费，保险费），是json格式的字符串：
```
xiaosi@yoona:/opt/apache-hive-2.0.0-bin/bin$ cat /home/xiaosi/test/train_order.txt
John	{"ticketPrice":"128", "servicePrice":"20", "insurancePrice":"5"}
Smith	{"ticketPrice":"318", "servicePrice":"30", "insurancePrice":"15"}
Ann	{"ticketPrice":"73", "servicePrice":"20", "insurancePrice":"2"}
White	{"ticketPrice":"67", "servicePrice":"15", "insurancePrice":"1"}
Green	{"ticketPrice":"645", "servicePrice":"40", "insurancePrice":"20"}
```
上传到HDFS的data/train_order路径下：
```
xiaosi@yoona:/opt/apache-hive-2.0.0-bin/bin$ hadoop fs -mkdir data/train_order
xiaosi@yoona:/opt/apache-hive-2.0.0-bin/bin$ hadoop fs -put /home/xiaosi/test/train_order.txt data/train_order
xiaosi@yoona:/opt/apache-hive-2.0.0-bin/bin$ hadoop fs -text data/train_order/train_order.txt
John	{"ticketPrice":"128", "servicePrice":"20", "insurancePrice":"5"}
Smith	{"ticketPrice":"318", "servicePrice":"30", "insurancePrice":"15"}
Ann	{"ticketPrice":"73", "servicePrice":"20", "insurancePrice":"2"}
White	{"ticketPrice":"67", "servicePrice":"15", "insurancePrice":"1"}
Green	{"ticketPrice":"645", "servicePrice":"40", "insurancePrice":"20"}
```
创建外部表train_order：
```
CREATE EXTERNAL TABLE train_order (name string, all_price String)
ROW FORMAT DELIMITED FIELDS
TERMINATED BY '\t'
ESCAPED BY ''
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION '/user/xiaosi/data/train_order';
```
#### 2.2 自定义Java类

自定义一个Java类，TrainOrderPriceSplitUDTF，这个类继承的是GenericUDTF接口，需要重新实现下面三个方法：
```
// in this method we specify input and output parameters: input ObjectInspector and an output struct
abstract StructObjectInspector initialize(ObjectInspector[] args) throws UDFArgumentException;
// here we process an input record and write out any resulting records
abstract void process(Object[] record) throws HiveException;
// this function is Called to notify the UDTF that there are no more rows to process. Clean up code or additional output can be produced here.
abstract void close() throws HiveException;
```
完整代码：
```java
package com.sjf.open.hive.udf.udtf;
import java.util.Iterator;
import java.util.List;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.apache.commons.lang3.StringUtils;
import org.apache.hadoop.hive.ql.exec.UDFArgumentException;
import org.apache.hadoop.hive.ql.metadata.HiveException;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDTF;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.PrimitiveObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.StructObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.PrimitiveObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.StringObjectInspector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.google.common.base.Objects;
import com.google.common.collect.Lists;
/**
 * Created by xiaosi on 16-11-24.
 */
public class TrainOrderPriceSplitUDTF extends GenericUDTF {
    private static final Logger logger = LoggerFactory.getLogger(TrainOrderPriceSplitUDTF.class);
    private StringObjectInspector stringObjectInspector;
    /**
     * The output struct represents a row of the table where the fields of the struct are the columns. The field names
     * are unimportant as they will be overridden by user supplied column aliases
     *
     * @param arguments
     * @return
     * @throws UDFArgumentException
     */
    @Override
    public StructObjectInspector initialize(ObjectInspector[] arguments) throws UDFArgumentException {
        // 参数个数检查
        if (arguments.length != 1) {
            throw new UDFArgumentException("train_order_price_split takes exactly one argument, but got " + arguments.length);
        }
        ObjectInspector argumentOne = arguments[0];
        // 参数类型检查
        if (!Objects.equal(argumentOne.getCategory(), ObjectInspector.Category.PRIMITIVE)) {
            throw new UDFArgumentException("The argument of function must be a string");
        }
        if (!Objects.equal(((StringObjectInspector) argumentOne).getPrimitiveCategory(),
                PrimitiveObjectInspector.PrimitiveCategory.STRING)) {
            throw new UDFArgumentException("The argument of function must be a string");
        }
        stringObjectInspector = (StringObjectInspector) argumentOne;
        // 列名 可以提供多列
        List<String> fieldNameList = Lists.newArrayList();
        fieldNameList.add("price");
        // 列类型
        List<ObjectInspector> fieldObjectInspectorList = Lists.newArrayList();
        fieldObjectInspectorList.add(PrimitiveObjectInspectorFactory.javaStringObjectInspector);
        return ObjectInspectorFactory.getStandardStructObjectInspector(fieldNameList, fieldObjectInspectorList);
    }
    /**
     * 数据处理
     *
     * @param field
     * @return
     */
    public List<Object[]> processInputRecord(String field) {
        List<Object[]> result = Lists.newArrayList();
        if (StringUtils.isBlank(field)) {
            logger.info("------------------ processInputRecord null");
            return result;
        }
        logger.info("-------------------- json : {}", field);
        try{
            Gson gson = new GsonBuilder().create();
            TrainOrderPrice trainOrderPrice = gson.fromJson(field, TrainOrderPrice.class);
            logger.info("-------------------- ticket price {} , service_price {}, insurance_price {} ", trainOrderPrice.getTicketPrice(), trainOrderPrice.getServicePrice(), trainOrderPrice.getInsurancePrice());
            result.add(new Object[]{trainOrderPrice.getTicketPrice()});
            result.add(new Object[]{trainOrderPrice.getServicePrice()});
            result.add(new Object[]{trainOrderPrice.getInsurancePrice()});
            return result;
        }
        catch (Exception e){
            result.add(new Object[]{"NULL"});
            return result;
        }
    }
    @Override
    public void process(Object[] record) throws HiveException {
        String field = stringObjectInspector.getPrimitiveJavaObject(record[0]).toString();
        if(StringUtils.isBlank(field)){
            logger.info("------------------- process null");
        }
        // 处理行
        List<Object[]> results = processInputRecord(field);
        Iterator<Object[]> iterator = results.iterator();
        while (iterator.hasNext()) {
            Object[] r = iterator.next();
            forward(r);
        }
    }
    @Override
    public void close() throws HiveException {
    }
}
```
`initialize`方法会被输入的每个参数调用，并最终传入到一个`ObjectInspector`对象中。这个方法的目标是检查参数类型，个数以及确定参数的返回类型。如果传入方法的类型是不合法的，这时用户同样可以向控制台抛出一个Exception异常信息。本函数只会返回一行数据，而且这行数据的数据类型确定为字符串。我们需要提供一个列名，不过这个并不是很重要，因为通常会被用户重新命名的类名覆盖。fieldNameList列表存储列名，fieldObjectInspectorList存储对应的列类型，因为这里是一个列表，我们可以设置返回多列，这这里我们先演示返回一列数据，下一个演示会演示返回队列数据。

`process`方法是实际进行处理的过程。需要注意的是，这个方法的返回类型是void。这是因为UDTF可以返回零行或者多行数据，而不像UDF，其只有唯一返回值。这种情况下会在for循环中对

`forward`方法进行多次调用，这样每调用一次就返回一行数据。forward方法的参数是一个数组，这样可以返回多列数据。

`processInputRecord`方法是我们自定义的一个方法，这个方法将传入的字符串转换为包含多列的多行数据(List<Object[]>)，list一个元素表示要输出的一行数据，Object数组表示输出一行数据中的多列。上面代码中传入的是一个json格式的字符串，我们需要反序列化得到每一个元素（ticketPrice,servicePrice,insurancePrice），将每一个元素作为一行输出。这里每行只有一列输出。

#### 2.3 演示

在Hive中使用与UDF一样，需要将Java代码进行编译，然后将编译后的UDF二进制类文件打包成一个Jar文件。然后，在Hive会话中，将这个Jar文件加入到类路径下，在通过CREATE FUNCTION 语句定义好使用这个Java类的函数。
```
hive (test)> add jar /home/xiaosi/code/openDiary/HiveCode/target/open-hive-1.0-SNAPSHOT.jar;
Added [/home/xiaosi/code/openDiary/HiveCode/target/open-hive-1.0-SNAPSHOT.jar] to class path
Added resources: [/home/xiaosi/code/openDiary/HiveCode/target/open-hive-1.0-SNAPSHOT.jar]
hive (test)> create temporary function price_split as 'com.sjf.open.hive.udf.udtf.TrainOrderPriceSplitUDTF';
OK
Time taken: 0.021 seconds
```
使用，我们的目标是将all_price字段中每一个元素作为一行输出：
```
hive (test)> select name, prices.price from train_order lateral view price_split(all_price) prices as price;
WARNING: Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. tez, spark) or using Hive 1.X releases.
Query ID = xiaosi_20161125174421_d50b7d7f-3a1b-4850-9491-01dcf9ae78c4
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there's no reduce operator
Job running in-process (local Hadoop)
2016-11-25 17:53:42,235 Stage-1 map = 100%,  reduce = 0%
Ended Job = job_local1692560833_0003
MapReduce Jobs Launched:
Stage-Stage-1:  HDFS Read: 1046 HDFS Write: 0 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
John	128
John	20
John	5
Smith	318
Smith	30
Smith	15
Ann	73
Ann	20
Ann	2
White	67
White	15
White	1
Green	645
Green	40
Green	20
Time taken: 1.285 seconds, Fetched: 15 row(s)
```
### 3. 可以产生具有多个字段的单行数据的UDTF

其原理跟上面是一样的，只不过细节不太一样。



这个内置函数，其有一个输入参数是一个URL链接，它还可以指定其他多个常数，来获取用户期望返回的特定部分：



这种类型的UDTF的好处是URL只需要被解析一次，然后就可以返回多个列。这显然是性能优势。而代替方式是：如果使用UDF的话，那么就需要写多个UDF，分别抽取其URL的特定部分，这样也消耗更长的时间。
