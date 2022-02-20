---
layout: post
author: sjf0115
title: Hadoop TotalOrderSorting 全排序
date: 2018-03-21 19:15:17
tags:
  - Hadoop

categories: Hadoop
permalink: hadoop-basics-total-order-sorting-mapreduce
---

在前面的部分中我们看到，当使用多个 Reducer 时，每个 Reducer 都接收分配给它们的 (key、value) 键值对。当一个 Reducer 接收到这些键值对时，它们按 key 进行排序，因此一般来说，Reducer 的输出也按 key 进行排序的。然而，不同的 Reducer 的输出之间并没有顺序排列，因此它们不能按顺序排列或顺序读取。

例如，有两个 Reducer，对简单的文本键进行排序，你可以有:
- Reducer 1 中输出: (a,5)， (d,6)， (w,5)
- Reducer 2 中输出: (b,2)， (c,5)， (e,7)
如果你单独看每一个输出，key 都是有序的，但是如果你一个一个地读取，顺序就会被打破。

`Total Order Sorting` 的目标是将不同 Reducer 之间的所有输出都排好序:
- Reducer 1 中输出: (a,5)， (b,2)， (c,5)
- Reducer 2 中输出: (d,6)， (e,7)， (w,5)

在这篇文章中，我们将首先看到如何使用自定义分区器手动创建全局排序。然后我们将学习如何使用 Hadoop 的 `TotalOrderPartitioner` 在简单类型的 key 上自动创建分区。最后，我们将看到一种更高级的技术，使用我们的 Secondary Sort 的 Composite Key（来自[上一篇文章](http://smartsi.club/2018/03/21/hadoop-basics-secondary-sort-in-mapreduce/)）与此分区器实现 "Total Secondary Sorting"。

### 1. 手动分区

在前面文章中，[Hadoop Secondary　Sort](http://smartsi.club/2018/03/21/hadoop-basics-secondary-sort-in-mapreduce/)使用了 `NaturalKeyPartiator`，根据自然 key ("state" 字段)的 hashcode 将 map 输出键值对分配给 Reducers。

实现全局排序的一种方法是实现 Partitioner 的 getPartition() 方法，以手动间隔地分配 key 给每一个 Reducer。例如，如果我们使用3个 Reducer，我们可以试着用这样的方法来均匀分配:
- Reducer 0：从 A 到 I 的 state 名称(包括9个字母)
- Reducer 1：从 J 到 Q 的 state 名称(包括8个字母)
- Reducer 2：从 R 到 Z 的 state 名称(包括9个字母)

如果这样做，可以简单地用以下方法来代替自然 key:
```java
import org.apache.hadoop.mapreduce.Partitioner;
import data.writable.DonationWritable;

public class CustomPartitioner extends Partitioner<CompositeKey, DonationWritable> {
    @Override
    public int getPartition(CompositeKey key, DonationWritable value, int numPartitions) {
        if (key.state.compareTo("J") < 0) {
            return 0;
        } else if (key.state.compareTo("R") < 0) {
            return 1;
        } else {
            return 2;
        }
    }
}
```
让我们再次执行这个任务，使用3个 Reducer 和我们的新自定义的分区器:
```
$ hadoop jar donors.jar mapreduce.donation.secondarysort.OrderByCompositeKey donors/donations.seqfile donors/output_secondarysort

$ hdfs dfs -ls -h donors/output_secondarysort
Found 4 items
-rw-r--r--   2 hduser supergroup          0 2015-12-28 23:27 donors/output_secondarysort/_SUCCESS
-rw-r--r--   2 hduser supergroup     32.9 M 2015-12-28 23:27 donors/output_secondarysort/part-r-00000
-rw-r--r--   2 hduser supergroup     29.8 M 2015-12-28 23:27 donors/output_secondarysort/part-r-00001
-rw-r--r--   2 hduser supergroup     12.0 M 2015-12-28 23:27 donors/output_secondarysort/part-r-00002

$ hdfs dfs -cat donors/output_secondarysort/part-r-00000 | head -n 3
c8e871528033bd9ce6b267ed8df27698        AA Canada 100.00
6eb5a716f73260c53a76a5d2aeaf3820        AA Canada 100.00
92db424b01676e462eff4c9361799c18        AA Canada 98.36

$ hdfs dfs -cat donors/output_secondarysort/part-r-00000 | tail -n 3
767e75dd5f7cb205b8f37a7a5ea68403        IN Zionsville 1.00
79f3e2549be8fea00ae65fed3143b8de        IN Zionsville 1.00
adcd76454acb15743fa2761a8aebc7b9        IN zionsville 0.94

$ hdfs dfs -cat donors/output_secondarysort/part-r-00001 | head -n 3
a370876d2717ed9d52750b1199362e05        KS 11151 25.00
9b416f7760c0717c222130418c656eb9        KS 11151 25.00
f0c6dd10268c37fee0d5eeeafc81040c        KS Abilene 100.00

$ hdfs dfs -cat donors/output_secondarysort/part-r-00001 | tail -n 3
bc214dd60705364cae4d5edb7b2fde96        PR TOA BAJA 25.00
aaa549ef89fe0a2668013a5c7f37ec55        PR Trujillo Alto 150.00
00da7cd5836b91d857ad1c62b4080a14        PR Trujillo Alto 15.00

$ hdfs dfs -cat donors/output_secondarysort/part-r-00002 | head -n 3
1fde8075005c72f2ca20bd5c1cb631a2        RI Adamsville 50.00
4a62f4e2de2ca06e8f84ca756992bcca        RI Albion 50.00
1f3e940d0a2bbb56bc260a4c17ca3855        RI Albion 25.00

$ hdfs dfs -cat donors/output_secondarysort/part-r-00002 | tail -n 3
f0a9489e53a203e0f7f47e6a350bb19a        WY Wilson 1.68
8aed3aba4473c0f9579927d0940c540f        WY Worland 75.00
1a497106ff2e2038f41897248314e6c6        WY Worland 50.00
```
这样就产生了一个正确的完全排序的3个文件结果。如果我们查看每个输出文件的开头和结尾，我们可以看到每个 state 都只属于一个 Reducer。我们还可以看到在所有输出文件上的 state 排序的延续。

然而，使用这种方法会有一些问题:
- 这需要手动编码。如果我们想要使用4个 Reducer，我们需要重新编写一个分区器。
- Reducer 之间的负载不均衡。第一个输出文件比最后一个输出文件大3倍。我们尽力把字母表中的26个字母分开，但现实是，state 名称并不是均匀分布在字母表上的。
为了解决这些问题，Hadoop 引入了一个强大但复杂的分区器 `TotalOrderPartitioner`。

### 2. TotalOrderPartitioner

`TotalOrderOrderPartitioner` 与我们的自定义类一样，但能动态的在各 Reducer 之间的均衡负载。为此，它需要对输入数据进行采样，来预计算在 Map 阶段开始之前如何将输入数据 "分隔" 成相等的部分。然后在 mapper 的分区阶段使用这些 "分割" 作为分区边界。

#### 2.1 对数据集采样

让我们首先创建一个比较简单的数据集来解释和测试 `TotalOrderPartitioner` 是如何工作的。[GenerateListOfStateCity.java](https://github.com/nicomak/blog/blob/master/donors/src/main/java/mapreduce/donation/totalorderpartitioner/GenerateListOfStateCity.java) MapReduce 作业简单地从 "捐赠" 序列文件中打印出文本键值对(state，city):
```java
package mapreduce.donation.totalorderpartitioner;

import java.io.IOException;
import java.util.Random;

import org.apache.commons.lang.StringUtils;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.SequenceFileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

import data.writable.DonationWritable;

public class GenerateListOfStateCity {

	private static final String RAND_SEPARATOR = ":";

	public static class RandomPrependingMapper extends Mapper<Object, DonationWritable, Text, Text> {

		private Text state = new Text();
		private Text city = new Text();
		private Random rand = new Random();

		@Override
		public void map(Object key, DonationWritable donation, Context context) throws IOException, InterruptedException {

			// Ignore rows where the donor state or city are not defined
			if (StringUtils.isEmpty((donation.donor_state)) || StringUtils.isEmpty(donation.donor_city)) {
				return;
			}

			state.set(rand.nextInt() + RAND_SEPARATOR + donation.donor_state);
			city.set(rand.nextInt() + RAND_SEPARATOR + donation.donor_city);
			context.write(state, city);
		}
	}

	public static class RandomTokenRemovalReducer extends Reducer<Text, Text, Text, Text> {

		private Text stateName = new Text();
		private Text cityName = new Text();

		@Override
		public void reduce(Text key, Iterable<Text> values, Context context) throws IOException, InterruptedException {

			for (Text value : values) {
				stateName.set(StringUtils.substringAfter(key.toString(), RAND_SEPARATOR));
				cityName.set(StringUtils.substringAfter(value.toString(), RAND_SEPARATOR));
				context.write(stateName, cityName);
			}
		}
	}

	public static void main(String[] args) throws Exception {

		Job job = Job.getInstance(new Configuration(), "Generate unordered list of (State,City)");
		job.setJarByClass(GenerateListOfStateCity.class);

		// Mapper configuration
		job.setMapperClass(RandomPrependingMapper.class);
		job.setInputFormatClass(SequenceFileInputFormat.class);
		job.setMapOutputKeyClass(Text.class);
		job.setMapOutputValueClass(Text.class);

		// Reducer configuration
		job.setReducerClass(RandomTokenRemovalReducer.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(Text.class);
		job.setNumReduceTasks(2);

		FileInputFormat.setInputPaths(job, new Path(args[0]));
		FileOutputFormat.setOutputPath(job, new Path(args[1]));
		System.exit(job.waitForCompletion(true) ? 0 : 1);

	}

}
```
输出结果：
```
$ hadoop jar donors.jar mapreduce.donation.secondarysort.totalorder.GenerateListOfStateCity donors/donations.seqfile donors/output_list_state_cities

$ hdfs dfs -ls -h donors/output_list_state_cities
Found 3 items
-rw-r--r--   2 hduser supergroup          0 2015-12-30 16:24 donors/output_list_state_cities/_SUCCESS
-rw-r--r--   2 hduser supergroup      9.3 M 2015-12-30 16:24 donors/output_list_state_cities/part-r-00000
-rw-r--r--   2 hduser supergroup      9.3 M 2015-12-30 16:24 donors/output_list_state_cities/part-r-00001

$ hdfs dfs -cat donors/output_list_state_cities/part-r-00000 | head
IL      Chicago
CA      Canyon Country
MN      Sartell
CA      San Francisco
TX      Murchison
TX      Austin
ID      Blackfoot
```

#### 2.2 TotalOrderPartitioner 工作流程

使用我们刚刚生成的简单数据集，这里有一个关于 `TotalOrderPartiationer` 如何帮助我们在多个 reducer 中对输入进行排序的说明:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/hadoop-basics-total-order-sorting-mapreduce-1.png?raw=true)

以下是整个过程的一些重要细节:

(1) `InputSampler` 在所有的 InputSplits 上对 key 进行采样，并使用作业的 SortComparator 对它们进行排序。Hadoop 库中有不同的输入采样器实现:
- `RandomSampler`:根据给定频率随机采样。这是我们在这个例子中使用的。
- `IntervalSampler`:定期取样(例如每5条记录)。
- `SplitSampler`:从每个 splits 中获取前 n 个样本。

(2) 输入采样器在 HDFS 中写入一个 "分区文件" 序列文件，它根据已排序的样本划分不同的分区边界。
- 对于n个 reducer，有 n-1 个边界写在这个文件上。在这个例子中有3个 reducer，所以2个边界被创建: "MD" 和 "PA"。

(3) MapReduce 任务从 mapper 任务开始。对于分区，mappers 使用 TotalOrderPartitioner，它将从 HDFS 读取分区文件以获取分区边界。然后，每个 map 输出都存储在基于这些边界的分区中。

(4) 在 shuffle 之后，每个 reducer 都从每个 mapper 拉取了一个 (key, value) 键值对的排好序的分区。在这一点上，reducer 2 上的所有键都比 reducer 1 中的所有键都要大(按字母顺序)，它比 reducer 0 中的所有键都要大。每个 reducer 合并它们已排好序的分区(使用排序的 merge-queue)并将其输出写入到 HDFS 中。

#### 2.3 Java Code for the Example

这里是代码，对于这个示例作业，你也可以在[GitHub](https://github.com/nicomak/blog/blob/master/donors/src/main/java/mapreduce/donation/totalorderpartitioner/TotalOrderPartitionerExample.java)上看到:
```java
package mapreduce.donation.totalorderpartitioner;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.KeyValueTextInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.partition.InputSampler;
import org.apache.hadoop.mapreduce.lib.partition.TotalOrderPartitioner;

public class TotalOrderPartitionerExample {

	public static void main(String[] args) throws Exception {

		// Create job and parse CLI parameters
		Job job = Job.getInstance(new Configuration(), "Total Order Sorting example");
		job.setJarByClass(TotalOrderPartitionerExample.class);

		Path inputPath = new Path(args[0]);
		Path partitionOutputPath = new Path(args[1]);
		Path outputPath = new Path(args[2]);

		// The following instructions should be executed before writing the partition file
		job.setNumReduceTasks(3);
		FileInputFormat.setInputPaths(job, inputPath);
		TotalOrderPartitioner.setPartitionFile(job.getConfiguration(), partitionOutputPath);
		job.setInputFormatClass(KeyValueTextInputFormat.class);
		job.setMapOutputKeyClass(Text.class);
		job.setMapOutputValueClass(Text.class);

		// Write partition file with random sampler
		InputSampler.Sampler<Text, Text> sampler = new InputSampler.RandomSampler<>(0.01, 1000, 100);
		InputSampler.writePartitionFile(job, sampler);

		// Use TotalOrderPartitioner and default identity mapper and reducer
		job.setPartitionerClass(TotalOrderPartitioner.class);
		job.setMapperClass(Mapper.class);
		job.setReducerClass(Reducer.class);

		FileOutputFormat.setOutputPath(job, outputPath);
		System.exit(job.waitForCompletion(true) ? 0 : 1);

	}

}
```
这是一种非常简单的工作，只需要使用 TotalOrderPartitioner。我们不需要创建特定的 Mapper 和 Reducer 类，因为我们只对输入进行排序，而不改变任何值或格式。默认的 Mapper 和 Reducer 类将会这样做。这里需要注意的是:

我们使用带有以下参数的 RandomSampler：
- freq = 0.01：采样器将遍历所有记录，每条记录被选为样本的概率为 0.01（= 1％）。
- numSamples = 1000：最多 1000 个样本。如果达到最大样本数量，则每个新选择的记录将替换已有的样本中记录。
- maxSplitsSampled = 100：最多采样100个分割。在我们的例子中，只有 2 个分割，所以这个最大值不会被应用。

InputSampler.writePartitionFile() 命令是一个阻塞调用。它将使用以下配置，必须事先指定：
- 作业的输入路径：作为采样的输入。
- reduce 任务的数量：写入到包含分区边界的 "分区文件" 序列文件。
- map 输出键类：惹恼我们！ 好吧，我可能夸大了一点。稍后会说明...

#### 2.4 执行与分析

```
$ hadoop jar donors.jar mapreduce.donation.totalorderpartitioner.TotalOrderPartitionerExample \
donors/output_list_state_cities \
donors/states_partitions.seqfile \
donors/output_totalorder_example

15/12/30 18:06:30 INFO input.FileInputFormat: Total input paths to process : 2
15/12/30 18:06:33 INFO partition.InputSampler: Using 1000 samples
...

$ hdfs dfs -cat donors/states_partitions.seqfile
SEQ♠↓org.apache.hadoop.io.Text!org.apache.hadoop.io.NullWritable *org.apache.hadoop.io.compress.DefaultCodec    99
Æ9ö
êB{2üZ}ö♥¬☻   ♂   ♥☻FLx9c♥      ♂   ♥☻NYx9c♥

$ hdfs dfs -ls -h donors/output_totalorder_example
Found 4 items
-rw-r--r--   2 hduser supergroup          0 2015-12-30 18:07 donors/output_totalorder_example/_SUCCESS
-rw-r--r--   2 hduser supergroup      5.3 M 2015-12-30 18:07 donors/output_totalorder_example/part-r-00000
-rw-r--r--   2 hduser supergroup      7.0 M 2015-12-30 18:07 donors/output_totalorder_example/part-r-00001
-rw-r--r--   2 hduser supergroup      6.4 M 2015-12-30 18:07 donors/output_totalorder_example/part-r-00002

$ hdfs dfs -cat donors/output_totalorder_example/part-r-00001 | head
FL      Jacksonville
FL      Clermont
FL      Tampa

$ hdfs dfs -cat donors/output_totalorder_example/part-r-00001 | tail
NV      Henderson
NV      pahrump
NV      Las Vegas

$ hdfs dfs -cat donors/output_totalorder_example/part-r-00002 | head
NY      New York
NY      New York
NY      bronx
```
这一次，当我们执行任务时，我们有一个日志告诉我们将会取多少个样本。

我们指定的分区文件 donors/states_partitions.seqfile 在作业完成后不会从 HDFS 中删除，因此我们可以查看里面的内容。实际上它是压缩的，所以它看起来不太好看......但是我们可以看到（或猜测......）从上到下是：
- SEQ：序列文件 header。
- <K,V> 类型, 即 <Text,NullWritable>。
- 压缩编解码器类
- 两个看起来像美国的 state ! 在一些有趣的字符和unicode点之间，我们可以识别 FL 和 NY。

通过可视化输出，我们可以看到第二个输出以 FL state 开始，第三个输出以 NY 开始。

当然，city 并未排序，因为我们无法控制这些值如何进入 reduce 函数，因为我们没有使用二次排序。但是，我们成功地按照 state 对所有 reducer 进行了排序，并且输出文件的大小相当平衡，与上一节中的手动分区相比。我们还可以将作业配置中的 reduce 任务数量从3更改为4或10，而不必担心分区器。

#### 2.5 限制与烦恼

如前面在示例代码注释中所述，需要指定 map 输出键的类。它必须对应于采样器<K，V>键类。如果你尝试删除 setMapOutputKeyClass（Text.class） 语句，或者在调用 InputSampler.writePartitionFile（） 后使用它，则最终会出现此错误：
```
Exception in thread "main" java.io.IOException: wrong key class: org.apache.hadoop.io.Text is not class org.apache.hadoop.io.LongWritable
        at org.apache.hadoop.io.SequenceFile$RecordCompressWriter.append(SequenceFile.java:1383)
        at org.apache.hadoop.mapreduce.lib.partition.InputSampler.writePartitionFile(InputSampler.java:340)
        at mapreduce.donation.totalorderpartitioner.TotalOrderPartitionerExample.main(TotalOrderPartitionerExample.java:39)
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:57)
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
        at java.lang.reflect.Method.invoke(Method.java:601)
        at org.apache.hadoop.util.RunJar.run(RunJar.java:221)
        at org.apache.hadoop.util.RunJar.main(RunJar.java:136)
```
这引出了几个问题：

(1) 为什么我们为采样器指定 V 值类？它在我们之前看到的分区文件中存储了 <Text，NullWritable> 键值对，所以显然它不需要从输入中读取值。
- 可能是因为它更容易实现，因为在 MapReduce 中所有的都是 <K，V> 参数化的。尤其是读取/写入序列文件。

(2) 为什么要指定 map 键类？采样器的泛型类型已经反映了输入类型…
- 我不是很确定。我相信如果这些类型是独立的就更好了。这与下一个问题有关。

(3)


### 3. Using a different input for sampling
#### 3.1 Objective
#### 3.2 MapReduce Solution
#### 3.3 Execution and Analysis
### 4. Total Secondary Sort by Composite Key
#### 4.1 Objective
#### 4.2 Optimization
#### 4.3 MapReduce Solution
##### 4.3.1 The Custom InputFormat
##### 4.3.2 The Custom RecordReader
#### 4.4 Execution and Analysis



原文： http://blog.ditullio.fr/2016/01/04/hadoop-basics-total-order-sorting-mapreduce/
