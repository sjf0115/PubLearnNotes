
试图使用 rdd.foreach(println) 或者 rdd.map(println) 打印出元素的值。在一个机器上，输出 RDD 所有的元素的将会生成你期望的输出。然而，在 cluster 模式下是，stdout 会由执行器来调用，写在了执行器的标准输出上，而不是驱动器上。所以在驱动器上你就看不到 stdout 的输出类了。

为了在驱动器上输出所有的元素，一个你可以使用 collect 方法，先把这个 RDD 带到驱动器节点上： rdd.collect().foreach(println)。不过这中方法容易造成内存不足。因为 collect() 会把 RDD 实体拿进一个单独的机器中；如果仅仅需要输出 RDD 的一小部分元素，最安全的方式是使用 take(): rdd.take().foreach(println).

如果数据量比较大的时候，尽量不要使用collect函数，因为这可能导致Driver端内存溢出问题。

```java
resultRDD.collect().forEach(new Consumer<String>() {
    @Override
    public void accept(String s) {
        System.out.println("Collect: " + s);
    }
});

resultRDD.foreach(new VoidFunction<String>() {
    @Override
    public void call(String s) throws Exception {
        System.out.println("Foreach: " + s);
    }
});
```
