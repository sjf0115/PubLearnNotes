> 在 Flink 1.12.0 版本中进行了删除

所谓分流，就是将一条数据流拆分成完全独立的两条、甚至多条流。也就是基于一个 DataStream 拆分成多个完全平等的子 DataStream。一般来说，我们会定义一些筛选条件，将符合条件的数据拣选出来放到对应的流里。

使用 Split 实现分流需要在 split 算子中定义 OutputSelector，然后重写其中的 select 方法，将不同类型的数据进行标记，最后对返回的 SplitStream 使用 select 方法将对应的数据选择出来。如下所示将输入流拆分为奇数流和偶数流两个子数据流：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setParallelism(1);
//输入流
DataStreamSource<Integer> source = env.fromElements(1, 2, 3, 4, 5, 6, 7, 8);

// 分流
SplitStream<Integer> splitStream = source.split(new OutputSelector<Integer>() {
    @Override
    public Iterable<String> select(Integer num) {
        // 给数据打标
        List<String> tags = new ArrayList<>();
        if (num % 2 == 0) {
            // 偶数打标 EVEN
            tags.add("EVEN");
        } else {
            // 奇数打标 ODD
            tags.add("ODD");
        }
        return tags;
    }
});

// 偶数流
DataStream<Integer> evenStream = splitStream.select("EVEN");
// 奇数流
DataStream<Integer> oddStream = splitStream.select("ODD");

// 输出
evenStream.print("偶数");
oddStream.print("奇数");
```
需要注意的是 Split 只是对数据流中的数据进行标记，并没有实现数据流的真正拆分。例如上面示例中偶数打标为 EVEN、奇数打标为 ODD，在 Split 阶段只是完成了打标工作。要想真正完成数据流的拆分还需要通过 Select 算子来实现。例如上面示例中通过 EVEN 标记将偶数拆分为 evenStream 数据流，通过 ODD 标记将奇数拆分为 oddStream 数据流。

需要注意的是 Split 不支持连续分流，即不支持 `Split...Select...Split` 这样的模式：
```java
SplitStream<Integer> splitStream = source.split(xxx);
// 偶数流
DataStream<Integer> evenStream = splitStream.select("EVEN");
//奇数流
DataStream<Integer> oddStream = splitStream.select("ODD");

// 拆分奇数流 小于5的一个流 大于等于5的一个流
SplitStream<Integer> oddSplitStream = oddStream
        .split(new OutputSelector<Integer>() {
            @Override
            public Iterable<String> select(Integer num) {
                // 给数据打标
                List<String> tags = new ArrayList<>();
                if (num < 5) {
                    // 小于5
                    tags.add("LESS");
                } else {
                    //大于等于5
                    tags.add("MORE");
                }
                return tags;
            }
        });
// 输出
evenStream.print("偶数");
oddSplitStream.select("LESS").print("小于");
oddSplitStream.select("MORE").print("大于等于");
```
上述运行会抛出 `Consecutive multiple splits are not supported` 异常，即不支持上述模式的连续分流。具体请查阅[FLINK-5031](https://issues.apache.org/jira/browse/FLINK-5031) 和 [FLINK-11084](https://issues.apache.org/jira/browse/FLINK-11084)。

虽然不支持上述模式的连续分流，但可以支持 `Split...Select...Map...Split` 这种模式：
```java
SplitStream<Integer> oddSplitStream = oddStream
    .map(new MapFunction<Integer, Integer>() {
        @Override
        public Integer map(Integer num) throws Exception {
            return num;
        }
    })
    .split(new OutputSelector<Integer>() {
        @Override
        public Iterable<String> select(Integer num) {
            // 给数据打标
            List<String> tags = new ArrayList<>();
            if (num < 5) {
                // 小于5
                tags.add("LESS");
            } else {
                //大于等于5
                tags.add("MORE");
            }
            return tags;
        }
    });
```
实际效果如下：
```
小于> 1
偶数> 2
小于> 3
偶数> 4
大于等于> 5
偶数> 6
大于等于> 7
偶数> 8
```

Split 已经标注 `@Deprecated`，甚至在 Flink 1.12.0 版本中进行了删除。官方给出的替代方案是使用更灵活的侧输出(Side-Output)。Split 之所以被放弃，主要因素有如下几点：
- Split 的性能较低
- Split 的逻辑问题，具体参见 具体请查阅[FLINK-5031](https://issues.apache.org/jira/browse/FLINK-5031) 和 [FLINK-11084](https://issues.apache.org/jira/browse/FLINK-11084)
- 连续拆分的语义不是很清楚
- 主要原因是 Flink 提供了侧输出(Side-Output)。使用侧输出可以完成 Split 可以完成的所有事情，并且语义更清楚、性能更好。

> 具体可以查阅[FLINK-19083](https://issues.apache.org/jira/browse/FLINK-19083)
