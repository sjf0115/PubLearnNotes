

#### 2.8 聚合

内置的`DataFrames`函数提供了常用的聚合函数，例如count()，countDistinct()，avg()，max()，min()等。虽然这些函数是为DataFrames设计的，但Spark SQL也具有类型安全的版本，在Scala和Java中其中有一些使用在强类型数据集上(Spark SQL also has type-safe versions for some of them in Scala and Java to work with strongly typed Datasets)。此外，用户不必限于预定义的聚合函数，可以自己创建。

##### 2.8.1 非类型安全的用户自定义聚合函数

自定义聚合函数
```java
import org.apache.spark.sql.Row;
import org.apache.spark.sql.expressions.MutableAggregationBuffer;
import org.apache.spark.sql.expressions.UserDefinedAggregateFunction;
import org.apache.spark.sql.types.DataType;
import org.apache.spark.sql.types.DataTypes;
import org.apache.spark.sql.types.StructField;
import org.apache.spark.sql.types.StructType;

import java.util.ArrayList;
import java.util.List;

public class MyAverage extends UserDefinedAggregateFunction{

    private StructType inputSchema;
    private StructType bufferSchema;

    public MyAverage() {
        List<StructField> inputFields = new ArrayList<>();
        inputFields.add(DataTypes.createStructField("inputColumn", DataTypes.LongType, true));
        inputSchema = DataTypes.createStructType(inputFields);

        List<StructField> bufferFields = new ArrayList<>();
        bufferFields.add(DataTypes.createStructField("sum", DataTypes.LongType, true));
        bufferFields.add(DataTypes.createStructField("count", DataTypes.LongType, true));
        bufferSchema = DataTypes.createStructType(bufferFields);
    }

    // 聚合函数输入参数数据类型
    @Override
    public StructType inputSchema() {
        return inputSchema;
    }

    // 聚合函数缓冲数据的数据类型
    @Override
    public StructType bufferSchema() {
        return bufferSchema;
    }

    // 返回值的数据类型
    @Override
    public DataType dataType() {
        return DataTypes.DoubleType;
    }

    // 这个函数是否总是在相同的输入上返回相同的输出
    @Override
    public boolean deterministic() {
        return true;
    }

    // 初始化聚合缓冲区 缓冲区本身是一个Row
    // 除了提供标准方法　如在索引中检索值(例如 get() getBoolean())外
    // 还提供了更新其值的机会　缓冲区内的数组和映射仍然是不可变的
    @Override
    public void initialize(MutableAggregationBuffer buffer) {
        buffer.update(0, 0L);
        buffer.update(1, 0L);
    }

    // 使用input的新输入数据更新给定的聚合缓冲区buffer
    @Override
    public void update(MutableAggregationBuffer buffer, Row input) {
        if (!input.isNullAt(0)) {
            long updatedSum = buffer.getLong(0) + input.getLong(0);
            long updatedCount = buffer.getLong(1) + 1;
            buffer.update(0, updatedSum);
            buffer.update(1, updatedCount);
        }
    }

    // 合并两个聚合缓冲区并将更新的缓冲区值存储回buffer1
    @Override
    public void merge(MutableAggregationBuffer buffer1, Row buffer2) {
        long mergedSum = buffer1.getLong(0) + buffer2.getLong(0);
        long mergedCount = buffer1.getLong(1) + buffer2.getLong(1);
        buffer1.update(0, mergedSum);
        buffer1.update(1, mergedCount);
    }

    // 计算最终结果
    @Override
    public Object evaluate(Row buffer) {
        return ((double) buffer.getLong(0)) / buffer.getLong(1);
    }
}

```

使用：
```
// 注册自定义聚合函数
session.udf().register("myAverage", new MyAverage());
// 创建DataFrame
Dataset<Row> df = session.read().json(employeePath);
// 将DataFrame注册为SQL临时视图
df.createOrReplaceTempView("employees");
df.show();

Dataset<Row> result = session.sql("SELECT myAverage(salary) as average_salary FROM employees");
result.show();
```
输出结果：
```
+-------+------+
|   name|salary|
+-------+------+
|Michael|  3000|
|   Andy|  4500|
| Justin|  3500|
|  Berta|  4000|
+-------+------+

+--------------+
|average_salary|
+--------------+
|        3750.0|
+--------------+
```

##### 2.8.2 类型安全的用户自定义聚合函数

强类型数据集的用户自定义聚合围绕`Aggregator`抽象类开展工作。 例如，类型安全的用户自定义的平均值聚合函数可以如下所示：

Average：
```
package com.sjf.open.model;

import java.io.Serializable;

/**
 * Created by xiaosi on 17-6-7.
 */
public class Average implements Serializable{

    private long sum;
    private long count;

    public Average(){

    }

    public Average(long sum, long count) {
        this.sum = sum;
        this.count = count;
    }

    public long getSum() {
        return sum;
    }

    public void setSum(long sum) {
        this.sum = sum;
    }

    public long getCount() {
        return count;
    }

    public void setCount(long count) {
        this.count = count;
    }
}

```
Employee：
```
package com.sjf.open.model;

import java.io.Serializable;

/**
 * Created by xiaosi on 17-6-7.
 */
public class Employee implements Serializable{

    private String name;
    private long salary;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public long getSalary() {
        return salary;
    }

    public void setSalary(long salary) {
        this.salary = salary;
    }
}

```
自定义聚合函数MyAverage2：
```
package com.sjf.open.model;

import org.apache.spark.sql.Encoder;
import org.apache.spark.sql.Encoders;
import org.apache.spark.sql.expressions.Aggregator;

/**
 * Created by xiaosi on 17-6-7.
 */
public class MyAverage2 extends Aggregator<Employee, Average, Double>{

    // 聚合的零值 应满足b + zero = b的属性
    @Override
    public Average zero() {
        return new Average(0L, 0L);
    }

    // 组合两个值以产生一个新值 为了性能,函数可以修改buffer并返回,而不是构造一个新的对象
    @Override
    public Average reduce(Average buffer, Employee employee) {
        long newSum = buffer.getSum() + employee.getSalary();
        long newCount = buffer.getCount() + 1;
        buffer.setSum(newSum);
        buffer.setCount(newCount);
        return buffer;
    }

    // 合并两个中间值
    @Override
    public Average merge(Average b1, Average b2) {
        long mergedSum = b1.getSum() + b2.getSum();
        long mergedCount = b1.getCount() + b2.getCount();
        b1.setSum(mergedSum);
        b1.setCount(mergedCount);
        return b1;
    }

    // 转换聚合的输出
    @Override
    public Double finish(Average reduction) {
        return ((double) reduction.getSum()) / reduction.getCount();
    }

    // 指定中间值类型的编码器
    @Override
    public Encoder<Average> bufferEncoder() {
        return Encoders.bean(Average.class);
    }

    // 指定最终输出值类型的编码器
    @Override
    public Encoder<Double> outputEncoder() {
        return Encoders.DOUBLE();
    }
}

```
使用：
```
Encoder<Employee> employeeEncoder = Encoders.bean(Employee.class);
Dataset<Employee> ds = session.read().json(employeePath).as(employeeEncoder);
ds.show();

MyAverage2 myAverage2 = new MyAverage2();
// 将函数转换为TypedColumn 并赋予一个名称
TypedColumn<Employee, Double> averageSalary = myAverage2.toColumn().name("average_salary");
Dataset<Double> result = ds.select(averageSalary);
result.show();
```

输出结果：
```
+-------+------+
|   name|salary|
+-------+------+
|Michael|  3000|
|   Andy|  4500|
| Justin|  3500|
|  Berta|  4000|
+-------+------+

+--------------+
|average_salary|
+--------------+
|        3750.0|
+--------------+
```
