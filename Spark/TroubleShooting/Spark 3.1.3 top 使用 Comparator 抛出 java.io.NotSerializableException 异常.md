## 1. 问题

在如下代码中使用 Top 算子计算年龄 Top2 的用户：
```java
JavaRDD<Person> peopleRDD = sc.parallelize(Arrays.asList(
        new Person("Lucy", 10),
        new Person("Tom", 18),
        new Person("Jack", 21),
        new Person("LiLy", 15)
));
List<Person> personTop = peopleRDD.top(2, new Comparator<Person>() {
    @Override
    public int compare(Person o1, Person o2) {
        long age1 = o1.getAge();
        long age2 = o2.getAge();
        if (age1 > age2) {
            return 1;
        } else if (age1 < age2) {
            return -1;
        }
        return 0;
    }
});
for(Person person : personTop) {
    System.out.println(person);
}
```
但在运行过程中抛出如下异常：
```java
Exception in thread "main" org.apache.spark.SparkException: Task not serializable
	at org.apache.spark.util.ClosureCleaner$.ensureSerializable(ClosureCleaner.scala:416)
	at org.apache.spark.util.ClosureCleaner$.clean(ClosureCleaner.scala:406)
	at org.apache.spark.util.ClosureCleaner$.clean(ClosureCleaner.scala:162)
	at org.apache.spark.SparkContext.clean(SparkContext.scala:2459)
	at org.apache.spark.rdd.RDD.$anonfun$mapPartitions$1(RDD.scala:860)
	at org.apache.spark.rdd.RDDOperationScope$.withScope(RDDOperationScope.scala:151)
	at org.apache.spark.rdd.RDDOperationScope$.withScope(RDDOperationScope.scala:112)
	at org.apache.spark.rdd.RDD.withScope(RDD.scala:414)
	at org.apache.spark.rdd.RDD.mapPartitions(RDD.scala:859)
	at org.apache.spark.rdd.RDD.$anonfun$takeOrdered$1(RDD.scala:1515)
	at org.apache.spark.rdd.RDDOperationScope$.withScope(RDDOperationScope.scala:151)
	at org.apache.spark.rdd.RDDOperationScope$.withScope(RDDOperationScope.scala:112)
	at org.apache.spark.rdd.RDD.withScope(RDD.scala:414)
	at org.apache.spark.rdd.RDD.takeOrdered(RDD.scala:1512)
	at org.apache.spark.rdd.RDD.$anonfun$top$1(RDD.scala:1489)
	at org.apache.spark.rdd.RDDOperationScope$.withScope(RDDOperationScope.scala:151)
	at org.apache.spark.rdd.RDDOperationScope$.withScope(RDDOperationScope.scala:112)
	at org.apache.spark.rdd.RDD.withScope(RDD.scala:414)
	at org.apache.spark.rdd.RDD.top(RDD.scala:1489)
	at org.apache.spark.api.java.JavaRDDLike.top(JavaRDDLike.scala:617)
	at org.apache.spark.api.java.JavaRDDLike.top$(JavaRDDLike.scala:616)
	at org.apache.spark.api.java.AbstractJavaRDDLike.top(JavaRDDLike.scala:45)
	at com.spark.example.core.base.ActionFunctionExample.topFunction(ActionFunctionExample.java:114)
	at com.spark.example.core.base.ActionFunctionExample.main(ActionFunctionExample.java:152)
Caused by: java.io.NotSerializableException: com.spark.example.core.base.ActionFunctionExample$3
Serialization stack:
	- object not serializable (class: com.spark.example.core.base.ActionFunctionExample$3, value: com.spark.example.core.base.ActionFunctionExample$3@38792286)
	- field (class: scala.math.LowPriorityOrderingImplicits$$anon$4, name: cmp$1, type: interface java.util.Comparator)
	- object (class scala.math.LowPriorityOrderingImplicits$$anon$4, scala.math.LowPriorityOrderingImplicits$$anon$4@782be4eb)
	- field (class: scala.math.Ordering$$anon$1, name: $outer, type: interface scala.math.Ordering)
	- object (class scala.math.Ordering$$anon$1, scala.math.Ordering$$anon$1@245ec1a6)
	- element of array (index: 1)
	- array (class [Ljava.lang.Object;, size 2)
	- field (class: java.lang.invoke.SerializedLambda, name: capturedArgs, type: class [Ljava.lang.Object;)
	- object (class java.lang.invoke.SerializedLambda, SerializedLambda[capturingClass=class org.apache.spark.rdd.RDD, functionalInterfaceMethod=scala/Function1.apply:(Ljava/lang/Object;)Ljava/lang/Object;, implementation=invokeStatic org/apache/spark/rdd/RDD.$anonfun$takeOrdered$2:(ILscala/math/Ordering;Lscala/collection/Iterator;)Lscala/collection/Iterator;, instantiatedMethodType=(Lscala/collection/Iterator;)Lscala/collection/Iterator;, numCaptured=2])
	- writeReplace data (class: java.lang.invoke.SerializedLambda)
	- object (class org.apache.spark.rdd.RDD$$Lambda$726/462911221, org.apache.spark.rdd.RDD$$Lambda$726/462911221@36bf84e)
	at org.apache.spark.serializer.SerializationDebugger$.improveException(SerializationDebugger.scala:41)
	at org.apache.spark.serializer.JavaSerializationStream.writeObject(JavaSerializer.scala:47)
	at org.apache.spark.serializer.JavaSerializerInstance.serialize(JavaSerializer.scala:101)
	at org.apache.spark.util.ClosureCleaner$.ensureSerializable(ClosureCleaner.scala:413)
	... 23 more
```

## 2. 解决方案

这种问题一般都是对象没有序列化导致的。起初以为是 Person 对象没有序列化，检查发现已经完成序列化：
```java
public class Person implements Serializable {
```
最后思考是不是 Comparator 这个接口没有实现序列化，检查发现确实没有序列化：
```java
public interface Comparator<T> {
    int compare(T o1, T o2);
    ...
}
```
所以解决方案是实现一个序列化的 Comparator：
```java
public interface SerializableComparator<T> extends Comparator<T>, Serializable {

}
```
执行代码中的 Comparator 修改为 SerializableComparator 即可：
```java
List<Person> personTop = peopleRDD.top(2, new SerializableComparator<Person>() {
    @Override
    public int compare(Person o1, Person o2) {
        long age1 = o1.getAge();
        long age2 = o2.getAge();
        if (age1 > age2) {
            return 1;
        } else if (age1 < age2) {
            return -1;
        }
        return 0;
    }
});
```
