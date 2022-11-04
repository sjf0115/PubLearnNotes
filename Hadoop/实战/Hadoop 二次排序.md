---
layout: post
author: sjf0115
title: Hadoop 二次排序
date: 2018-03-21 14:15:17
tags:
  - Hadoop

categories: Hadoop
permalink: hadoop-basics-secondary-sort-in-mapreduce
---

我们首先提出了一个查询问题，为了解决这个问题，需要在数据集的多个字段上进行排序。然后，我们将研究 MapReduce `Shuff` 阶段的工作原理，然后再实现我们的二次排序以获得我们想要的查询结果。

### 1. 查询

如果我们想查看指定 `state` 和 `city` 的所有捐款者的 `id`，`state`，`city` 以及捐款总额 `total`。按以下顺序排列结果：
- `state` - 按字母顺序升序排序（不区分大小写）
- `city` - 按字母顺序升序排序（不区分大小写）
- `total` - 按数字顺序降序排序

可以用 SQL 如下实现：
```sql
SELECT donation_id, donor_state, donor_city, total
FROM donations
WHERE donor_state IS NOT NULL AND donor_city IS NOT NULL
ORDER BY lower(donor_state) ASC, lower(donor_city) ASC, total DESC;
```

### 2. 理解 Shuffle 阶段

现在我们需要深入了解 `Shuffle` 阶段：
- 如何和在哪里工作
- 有哪些工具可以根据我们的需求进行自定义以及调整

以下是使用 2 个 mapper 以及 2 个 reducer 任务的工作流程图：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-basics-secondary-sort-in-mapreduce-1.jpg?raw=true)

关于不同编号的步骤的一些细节：
- (1) `mapper` 的 `map` 方法从 InputFormat 提供的分片中接收所有 `（key，value）` 键值对。这是我们通常在 Mapper 中编写的最重要的方法。
- (2) 使用指定的分区器为每个用户的 `map` 方法输出进行分区。默认情况下，在 `MapReduce` 中使用 `HashPartitioner`。它使用 key 的 `hashCode（）` 值并对 `reducer` 的个数进行取模。这将根据 key 随机确定（key，value） 键值对存储在每个 `Reducer` 的不同分区中。所有具有相同 key 的键值对位于同一个分区中，并在相同的 reducer 中结束。
- (3) 在写入磁盘之前，使用指定的 `Sort Comparator` 对数据进行排序。同一分区记录全部写入同一个临时文件。
- (4) `reducer` 从所有 `mapper` 中拉取所有分配给他们的分区。分区可以写入本地临时文件，或者足够小时存储在内存中。这个过程也被称为 `Shuffle`，因为分区正在洗牌。
- (5) `Sort Comparator` 在合并所有内存和磁盘中的分区时再次使用。每个 `reducer` 都有一个所有`（key, value）`键值对完全排序的列表，这些键值对是分区器分配给它们的所有键的。
- (6) `Group Comparator` 用于将值分组成列表。每个 "不同" key，都将调用带有参数（`key，list<values>`）的 `reduce` 方法。

### 3. 二次排序

二次排序是一种可用于在多个字段上排序数据的技术。它依赖于使用一个复合键，它将包含我们想要用于排序的所有值。

在本文中，读取 `donations Sequence File`，并在 `shuffling`和 `reducing` 之前将每个捐赠记录映射为`（CompositeKey，DonationWritable）` 键值对。

> 本文中使用的所有类都可以在GitHub上查看：https://github.com/nicomak/blog/tree/master/donors/src/main/java/mapreduce/donation/secondarysort。

为了得到查询结果而执行的 MapReduce 二次排序作业位于同一个包的 [OrderByCompositeKey.java](https://github.com/nicomak/blog/blob/master/donors/src/main/java/mapreduce/donation/secondarysort/OrderByCompositeKey.java) 文件中。

```java
package mapreduce.donation.secondarysort;

import java.io.IOException;

import org.apache.commons.lang.StringUtils;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
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

public class OrderByCompositeKey {
	public static final Log LOG = LogFactory.getLog(OrderByCompositeKey.class);
	public static class CompositeKeyCreationMapper extends Mapper<Object, DonationWritable, CompositeKey, DonationWritable> {
		private CompositeKey compositeKey = new CompositeKey();
		@Override
		public void map(Object key, DonationWritable donation, Context context) throws IOException, InterruptedException {

			// Ignore entries with empty values for better readability of results
			if (StringUtils.isEmpty(donation.donor_state) || StringUtils.isEmpty(donation.donor_city)) {
				return;
			}
			compositeKey.set(donation.donor_state, donation.donor_city, donation.total);
			context.write(compositeKey, donation);
		}
	}

	public static class ValueOutputReducer extends Reducer<CompositeKey, DonationWritable, Text, Text> {
		private Text outputKey = new Text();
		private Text outputValue = new Text();
		@Override
		public void reduce(CompositeKey key, Iterable<DonationWritable> donations, Context context) throws IOException, InterruptedException {

			for (DonationWritable donation : donations) {
				outputKey.set(donation.donation_id);
				outputValue.set(String.format("%s %s %.2f", donation.donor_state, donation.donor_city, donation.total));
				context.write(outputKey, outputValue);
			}
		}
	}

	public static void main(String[] args) throws Exception {

		Job job = Job.getInstance(new Configuration(), "Secondary Sorting");
		job.setJarByClass(OrderByCompositeKey.class);

		// Mapper configuration
		job.setMapperClass(CompositeKeyCreationMapper.class);
		job.setInputFormatClass(SequenceFileInputFormat.class);
		job.setMapOutputKeyClass(CompositeKey.class);
		job.setMapOutputValueClass(DonationWritable.class);

		// Partitioning/Sorting/Grouping configuration
		job.setPartitionerClass(NaturalKeyPartitioner.class);
		job.setSortComparatorClass(FullKeyComparator.class);
		job.setGroupingComparatorClass(NaturalKeyComparator.class);

		// Reducer configuration
		job.setReducerClass(ValueOutputReducer.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(Text.class);
		job.setNumReduceTasks(1);

		FileInputFormat.setInputPaths(job, new Path(args[0]));
		FileOutputFormat.setOutputPath(job, new Path(args[1]));

		System.exit(job.waitForCompletion(true) ? 0 : 1);
	}

}
```

#### 3.1 Composite Key

我们想对 3 个值进行排序，所以我们创建了一个名为 [CompositeKey](https://github.com/nicomak/blog/blob/master/donors/src/main/java/mapreduce/donation/secondarysort/CompositeKey.java) 的 WritableComparable 类，具有如下 3 个属性：
- `state`（String） - 这个被用作分区的自然键（或主键）
- `city`（String） - 在同一个分区内对具有相同 `state` 自然键进行排序的辅助键（译者注：即同一分区内 `state` 相同将根据 `city` 进行排序）
- `total`（float） - 当 `city` 相同时进一步排序的另一个辅助键（译者注：在同一分区内 `state` 和 `city` 均相同则根据 `total` 进行排序）
```java
package mapreduce.donation.secondarysort;
import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import org.apache.hadoop.io.WritableComparable;

public class CompositeKey implements WritableComparable<CompositeKey> {

	public String state;
	public String city;
	public float total;

	public CompositeKey() {
	}

	public CompositeKey(String state, String city, float total) {
		super();
		this.set(state, city, total);
	}

	public void set(String state, String city, float total) {
		this.state = (state == null) ? "" : state;
		this.city = (city == null) ? "" : city;
		this.total = total;
	}

	@Override
	public void write(DataOutput out) throws IOException {
		out.writeUTF(state);
		out.writeUTF(city);
		out.writeFloat(total);
	}

	@Override
	public void readFields(DataInput in) throws IOException {
		state = in.readUTF();
		city = in.readUTF();
		total = in.readFloat();
	}

	@Override
	public int compareTo(CompositeKey o) {
		int stateCmp = state.toLowerCase().compareTo(o.state.toLowerCase());
		if (stateCmp != 0) {
			return stateCmp;
		} else {
			int cityCmp = city.toLowerCase().compareTo(o.city.toLowerCase());
			if (cityCmp != 0) {
				return cityCmp;
			} else {
				return Float.compare(total, o.total);
			}
		}
	}
}
```

> 我在这个类中实现了 compareTo（），但它只是默认的自然排序，所有字段都按升序比较。我们的查询想要对 `total` 字段进行降序排序，为此我们将在下一段中创建一个特定的 `Sort Comparator`。

#### 3.2 Sort Comparator

如图所示，如果我们希望我们的结果在 `CompositeKey` 的所有3个属性上按照我们期望的方式进行排序，则必须使用按照 `[state，city，-total]` 优先级顺序排序的 `Sort Comparator`。正如我们在前一部分中所做的那样，我们创建了一个继承 `WritableComparator` 并为我们的排序需求实现 `compare（）` 方法的类：
```java
import org.apache.hadoop.io.WritableComparable;
import org.apache.hadoop.io.WritableComparator;

public class FullKeyComparator extends WritableComparator {

    public FullKeyComparator() {
        super(CompositeKey.class, true);
    }

    @SuppressWarnings("rawtypes")
    @Override
    public int compare(WritableComparable wc1, WritableComparable wc2) {

        CompositeKey key1 = (CompositeKey) wc1;
        CompositeKey key2 = (CompositeKey) wc2;

        int stateCmp = key1.state.toLowerCase().compareTo(key2.state.toLowerCase());
        if (stateCmp != 0) {
            return stateCmp;
        } else {
            int cityCmp = key1.city.toLowerCase().compareTo(key2.city.toLowerCase());
            if (cityCmp != 0) {
                return cityCmp;
            } else {
                return -1 * Float.compare(key1.total, key2.total);
            }
        }
    }
}
```
然后，我们使用 `job.setSortComparatorClass（FullKeyComparator.class）` 将此类设置为 `Sort Comparator`。

现在使用单个 `reducer` 将给我们完全排序的结果。仅使用一个 `reducer` 时，实现 `Composite Key` 和 `Sort Comparator` 就足以对多个字段进行排序。

#### 3.3 Partitioner

如果我们使用多个 `reducer`，会发生什么？ 默认分区器 `HashPartitioner` 将根据 `CompositeKey` 对象的 `hashCode` 值将其分配给 `reducer`。无论我们是重写了 `hashcode()` 方法（正确使用所有属性的哈希）还是不重写（使用默认 `Object` 的实现，使用内存中地址），都将 "随机" 对所有 keys 进行分区。合并来自 `mappers` 的所有分区后，`reducer` 的 key 可能会像如下第一列所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-basics-secondary-sort-in-mapreduce-2.png?raw=true)

在第一个输出列中，在一个 `reducer` 内，对于给定 `state` 的数据按城市名称排序，然后按总捐赠量降序排列。但这种排序没有什么意义，因为有些数据丢失了。例如，`Reducer 0` 有2个排序的 `Los Angeles` key，但来自 `Reducer 1` 的 `Los Angeles` 条目应该放在这两个 key 之间。

因此，当使用多个 reducers 时，我们想要的是将具有相同 `state` 的所有 `（key，value）` 键值对发送给同一个 `reducer`，就像第二列显示的那样。最简单的方法是创建我们自己的 `NaturalKeyPartitioner`，类似于默认的 `HashPartitioner`，但仅基于 `state`  的 `hashCode`，而不是完整的 `CompositeKey` 的 `hashCode`：
```java
import org.apache.hadoop.mapreduce.Partitioner;
import data.writable.DonationWritable;

public class NaturalKeyPartitioner extends Partitioner<CompositeKey, DonationWritable> {
    @Override
    public int getPartition(CompositeKey key, DonationWritable value, int numPartitions) {
        // Automatic n-partitioning using hash on the state name
        return Math.abs(key.state.hashCode() & Integer.MAX_VALUE) % numPartitions;
    }
}
```
我们使用 `job.setPartitionerClass（NaturalKeyPartitioner.class）` 将此类设置为作业的分区器。

#### 3.4 Group Comparator

`Group Comparator` 决定每次调用 `reduce` 方法时如何对这些值分组（译者注：一个分组调用一次 `reduce` 方法）。

继续使用上图中的 `Reducer 0` 的例子。如果合并分区后，一个 reducer 中的（key，value）键值对必须如下处理：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-basics-secondary-sort-in-mapreduce-3.png?raw=true)

可以完成的可能分组如下：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-basics-secondary-sort-in-mapreduce-4.png?raw=true)

说明：
- 没有相同 `(state,city,total)` 组合的 keys。因此，对于第一个分组，每个记录调用一次 reduce 方法。
- 第二个是根据 `state, city` 分组。B 和 C 键值对的 key 有相同的 `state` 和 `city`，因此它们组合在一起在一个 `reducer()` 中调用。传递给函数的 key 是分组中第一个键值对的 key，因此它依赖于排序。
- 第三个只查看 `state`。B， C ，D 键值对中的 key 都具有相同的 `state`，因此它们被组合在一起以在一个 `reducer()` 中调用。

在某些情况下分组可能很有用。 例如，如果你想在每个捐赠输出旁边打印给定城市的所有捐款总和，则可以使用上述示例中的第二个分组。这样做，可以在输出所有值之前，将 `reduce()` 函数中的所有 "总计" 字段求和。

对于我们的查询，我们只需要打印出每个记录的字段，对于分组无关紧要。调用 `reduce()` 函数4次，3次或2次仍然会只打印出 A，B ，C 和 D 记录的 `（id，state，city，total）` 字段。 对于这个作业，它对性能没有任何影响。

让我们按照 `state`（`natural key`）进行分组，只是为了使用我们自己的 `Group Comparator`：
```java
import org.apache.hadoop.io.WritableComparable;
import org.apache.hadoop.io.WritableComparator;

public class NaturalKeyComparator extends WritableComparator {
    public NaturalKeyComparator() {
        super(CompositeKey.class, true);
    }
    @SuppressWarnings("rawtypes")
    @Override
    public int compare(WritableComparable wc1, WritableComparable wc2) {
        CompositeKey key1 = (CompositeKey) wc1;
        CompositeKey key2 = (CompositeKey) wc2;
        return key1.state.compareTo(key2.state);
    }
}
```
然后我们可以通过调用 `job.setGroupingComparatorClass（NaturalKeyComparator.class）` 来使用这个比较器。

### 4. 作业运行与结果

#### 4.1 Job 1 : With a single reducer

输出结果:
```
$ hadoop jar donors.jar mapreduce.donation.secondarysort.OrderByCompositeKey donors/donations.seqfile donors/output_secondarysort

$ hdfs dfs -ls -h donors/output_secondarysort
-rw-r--r--   2 hduser supergroup          0 2015-12-28 16:00 donors/output_secondarysort/_SUCCESS
-rw-r--r--   2 hduser supergroup     74.6 M 2015-12-28 16:00 donors/output_secondarysort/part-r-00000

$ hdfs dfs -cat donors/output_secondarysort/part-r-00000 | head -n 8
c8e871528033bd9ce6b267ed8df27698        AA Canada 100.00
6eb5a716f73260c53a76a5d2aeaf3820        AA Canada 100.00
92db424b01676e462eff4c9361799c18        AA Canada 98.36
e0f266ed8875df71f0012fdaf50ae22e        AA Canada 1.64
d9064b2494941725d0f93f6ca781cdc7        AA DPO 50.00
83b85744490320c8154f1f5bcd703296        AA DPO 25.00
7133a67b51c1ee61079fa47e3b9e5160        AA Fremont 50.00
f3475f346f1483dfb57efc152d3fbced        AA Helsinki\, FINLAND 153.39

$ hdfs dfs -cat donors/output_secondarysort/part-r-00000 | tail -n 8
10df7888672288077dc4f60e4a83bcc2        WY Wilson 114.98
0b4dda44ac5dc29a522285db56082986        WY Wilson 100.00
4276bc7e6df5f4643675e65bb2323281        WY Wilson 100.00
519da9b977281b7623d655b8ee0c8ea5        WY Wilson 91.47
92469f6f000a6cd66ba18b5fe03e6871        WY Wilson 23.32
f0a9489e53a203e0f7f47e6a350bb19a        WY Wilson 1.68
8aed3aba4473c0f9579927d0940c540f        WY Worland 75.00
1a497106ff2e2038f41897248314e6c6        WY Worland 50.00
```
分析:

由于只使用1个 reducer ，所以只有1个输出文件。该文件以状态 "AA" 开始，该 `state` 不是 `USA` `state`，但看起来是对国外城市的重新组合。该文件以 "WY" （怀俄明州）城市 `Wilson` 和 `Worland` 结束。所有内容都按照查询中的要求排序。

#### 4.2 Job 2 : With 3 reducers, using default partitioner

这次我们通过设置 `job.setNumReduceTasks（3）` 来使用3个 reducer，并且我们注释掉 `job.setPartitionerClass（NaturalKeyPartitioner.class）` 这一行来查看会发生什么。

输出结果:
```
$ hadoop jar donors.jar mapreduce.donation.secondarysort.OrderByCompositeKey donors/donations.seqfile donors/output_secondarysort

$ hdfs dfs -ls -h donors/output_secondarysort
-rw-r--r--   2 hduser supergroup          0 2015-12-28 15:36 donors/output_secondarysort/_SUCCESS
-rw-r--r--   2 hduser supergroup     19.4 M 2015-12-28 15:36 donors/output_secondarysort/part-r-00000
-rw-r--r--   2 hduser supergroup     38.7 M 2015-12-28 15:36 donors/output_secondarysort/part-r-00001
-rw-r--r--   2 hduser supergroup     16.5 M 2015-12-28 15:36 donors/output_secondarysort/part-r-00002

$ hdfs dfs -cat donors/output_secondarysort/part-r-00000 | tail -n 5
234600cf0c052b95e544f690a8deecfc        WY Wilson 158.00
10df7888672288077dc4f60e4a83bcc2        WY Wilson 114.98
0b4dda44ac5dc29a522285db56082986        WY Wilson 100.00
4276bc7e6df5f4643675e65bb2323281        WY Wilson 100.00
1a497106ff2e2038f41897248314e6c6        WY Worland 50.00

$ hdfs dfs -cat donors/output_secondarysort/part-r-00001 | tail -n 5
a31e6d2ddcffef3fb0c81a9b5be8a62b        WY Wilson 177.60
ab277b46c65df53305ceee436e775f86        WY Wilson 150.00
519da9b977281b7623d655b8ee0c8ea5        WY Wilson 91.47
92469f6f000a6cd66ba18b5fe03e6871        WY Wilson 23.32
8aed3aba4473c0f9579927d0940c540f        WY Worland 75.00

$ hdfs dfs -cat donors/output_secondarysort/part-r-00002 | tail -n 5
db2334f876e2a661dc66ec79b49a7073        WY Wilson 319.44
f740650269f523ac94a8bc54c40ffcb8        WY Wilson 294.70
dfdba1ed68a130da5337e28b45a469d1        WY Wilson 286.64
e5cf931220ab071083d174461ef50411        WY Wilson 278.19
f0a9489e53a203e0f7f47e6a350bb19a        WY Wilson 1.68
```

分析:

通过查看每个输出的最后5行，我们可以注意到所有输出都与 `Wilson` 城市有关。其中两项输出有 `Worland` 的条目。

正如前面所解释的，每个输出的结果都是按照 `state` 和 `city` 的上升顺序排列，并且 `donation` 降序排列。但是不可能查看给定 `state` 或 `city` 的所有排序捐赠，因为它们分布在多个文件中。

#### 4.3 Job 3 : With 3 reducers, using NaturalKeyPartitioner

对于这个作业，我们只需重新设置 `job.setPartitionerClass（NaturalKeyPartitioner.class）` 即可使用我们的自定义分区器，同时保留3个 Reducer 任务。

输出结果:
```
$ hadoop jar donors.jar mapreduce.donation.secondarysort.OrderByCompositeKey donors/donations.seqfile donors/output_secondarysort

$ hdfs dfs -ls -h donors/output_secondarysort
-rw-r--r--   2 hduser supergroup          0 2015-12-28 16:37 donors/output_secondarysort/_SUCCESS
-rw-r--r--   2 hduser supergroup     23.2 M 2015-12-28 16:37 donors/output_secondarysort/part-r-00000
-rw-r--r--   2 hduser supergroup     22.8 M 2015-12-28 16:37 donors/output_secondarysort/part-r-00001
-rw-r--r--   2 hduser supergroup     28.7 M 2015-12-28 16:37 donors/output_secondarysort/part-r-00002

$ hdfs dfs -cat donors/output_secondarysort/part-r-00000 | tail -n 5
eeac9e18795680ccc00f69a42ec4fbc5        VI St. Thomas 10.00
634f02e6ffc99fddd2b2c9cda7b7677c        VI St. Thomas 10.00
9f71710178a4fab17fb020bc994be60b        VI Zurich / Switzerland 75.00
f81b2dc07c0cc3ccea5941dc928247a5        VI Zurich / Switzerland 50.00
8337fac8a67e50ad4a0dfe7decc4b8e9        VI Zurich / Switzerland 50.00

$ hdfs dfs -cat donors/output_secondarysort/part-r-00001 | tail -n 5
9f3ea230d660a20ec91b287b8a0f6693        WI Wrightstown 5.00
8b95de5d2b2027c0a3d2631c9f0f6f9b        WI Wrightstown 5.00
9db66b1c0c71dd438a8f979dd04cdfb8        WI Wrightstown 5.00
c7c60406d260915cb35a7e267c28becc        WI Wrightstown 5.00
c2d98a640c301cf277247302ad5014ca        WI Wrightstown 5.00

$ hdfs dfs -cat donors/output_secondarysort/part-r-00002 | tail -n 5
519da9b977281b7623d655b8ee0c8ea5        WY Wilson 91.47
92469f6f000a6cd66ba18b5fe03e6871        WY Wilson 23.32
f0a9489e53a203e0f7f47e6a350bb19a        WY Wilson 1.68
8aed3aba4473c0f9579927d0940c540f        WY Worland 75.00
1a497106ff2e2038f41897248314e6c6        WY Worland 50.00
```

分析:

与 Job2 的输出相比，我们可以看到只有一个 reducer（r-00002） 具有来自 `WY` `state`（怀俄明州）的条目。因此，如果你只对来自 `WY` 的捐款感兴趣，那么你要查找的结果是完整且正确地排序在一个文件中的。

其他 reducer 输出以不同 `state`（"VI" 和 "WI"）结束，因为每个 `state` 都是独占一个 reducer。这是因为我们告诉我们的 `NaturalKeyPartitioner` 将 `state` 字段视为划分的决定性值。

#### 4.4 Performance Comparison

这里是本文中描述的3个作业的比较表。取自资源管理器用户界面的总时间。其他值来自MR历史服务器UI。所有指标均为2次执行的平均值。

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-basics-secondary-sort-in-mapreduce-5.png?raw=true)

使用3个 reducer 时，我们可以观察到总执行时间显着改善。Job2和3比Job1更快。在Job2和Job3中，每个 reducer 的shuffling/merging的时间更长一些，但是实际时间要短得多。

### 5. 结论

在这一部分中，我们学习了如何使用一些工具在 Shuffle 阶段对分区，排序和分组进行更多控制。

我们看到了如何实现二次排序，这有助于我们：
- 当使用单个 reducer 时，对多个字段的数据集进行完全排序
- 当使用多个 reducer 时，在辅助键上对有相同 `natural key` 的记录进行排序。

使用多个 `reducer` 可以加快排序过程，但代价是只能对多个 `reducer` 实现在 `natural key` 上的部分排序。

#### 5.1 新定义

事后看来，回顾我们应用于复合 key 的不同工具的效果，除了 "在多个字段上进行排序" 外，我们还可以给出二次排序的更一般而精确的定义：

二次排序是一种技术，用于控制 Reducer 的输入对 `如何` 传递给 reduce 函数。

上面的 `如何` 可以理解为以何种顺序（`Sort Comparator`）以及基于 key 的对值进行分组的方式（`Group Comparator`）

根据这个定义，使用 `Secondary Sort`，我们可以对 `Reducer` 内的数据进行全面控制，这就是输出文件内部始终排好序的原因。

#### 5.2 下一步

使用 `Secondary Sort`，我们可以控制 `Reducer` 内的数据，但我们无法控制如何将已排序的 map 输出分发给 reducer。我们已经定义了一个分区器来确保不同的 reducer 管理他们自己的 `natural keys` 并保证在二级键的排序。但它并没有解决在所有输出中对所有 `natural keys ` 进行排序的问题。

在下一篇文章中，我们将学习如何使用全排序（`Total Order Sorting`）来做到这一点。

原文： http://blog.ditullio.fr/2015/12/28/hadoop-basics-secondary-sort-in-mapreduce/
