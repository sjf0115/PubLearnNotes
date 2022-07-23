Partitioner控制Map中间输出数据key的分区。key（或key的子集）通常通过哈希函数来生成分区。分区的总数与作业的Reduce任务个数相同。因此，这控制了中间key发送给m个任务中的哪一个。

注意：如果要求Partitioner类获取作业的配置对象，需要实现`Configurable`接口。

```java
@InterfaceAudience.Public
@InterfaceStability.Stable
public abstract class Partitioner<KEY, VALUE> {

 /**
 * @param key the key to be partioned.
 * @param value the entry value.
 * @param numPartitions the total number of partitions.
 * @return the partition number for the <code>key</code>.
 */
  public abstract int getPartition(KEY key, VALUE value, int numPartitions);

}
```
getPartition函数的作用是给定一个key(表示一个记录)以及分区总个数(例如，作业的Reduce任务的个数)，获取给定key的分区号。

### 1. HashPartitioner

HashPartitioner是Partitioner默认实现，是一种基于哈希值的分区方法:
```java
@InterfaceAudience.Public
@InterfaceStability.Stable
public class HashPartitioner<K, V> extends Partitioner<K, V> {
  /* 使用hashCode()实现分区 */
  public int getPartition(K key, V value, int numReduceTasks) {
    return (key.hashCode() & Integer.MAX_VALUE) % numReduceTasks;
  }
}
```
### 2. BinaryPartitioner

BinaryPatitioner继承于Partitioner<BinaryComparable ,V>，是Partitioner<k,v>的偏特化子类。该类提供leftOffset和rightOffset，在计算键值key对应的Reduce任务时仅对键值K的[rightOffset，leftOffset]区间进行哈希。

#### 2.1 配置

用于分区的子数组可以用过如下属性来配置:

配置属性|属性值|默认值
---|---|---
mapreduce.partition.binarypartitioner.left.offset|数组左偏移量|0
mapreduce.partition.binarypartitioner.right.offset|数组右偏移量|-1

与Python中一样，允许负偏移和正偏移，但意义略有不同。例如，在长度为5的数组的情况下，可能的偏移量为:

B|B|B|B|B
---|---|---|---|---
0|1|2|3|4
-5|-4|-3|-2|-1

第一行数字给出了偏移0 ...4在数组中的位置;第二行给出对应的负偏移。与Python相反，指定子数组的字节i和j作为第一个和最后一个元素(byte[i,j])，分别当i和j是左右偏移量时(the specified subarray has byte i and j as first and last element, repectively, when i and j are the left and right offset)。

使用Java编写Hadoop程序时，建议使用以下静态方便方法来设置偏移量：
```java
setOffsets
setLeftOffset
setRightOffset
```
#### 2.2 字段

LEFT_OFFSET_PROPERTY_NAME 用于配置左偏移量

RIGHT_OFFSET_PROPERTY_NAME 用于配置右偏移量

#### 2.3 方法
返回值|方法名|描述
---|---|---
Configuration|getConf()|返回此对象使用的配置。
int|getPartition(BinaryComparable key, V value, int numPartitions)|使用(通过该方法对返回的数组的进行切割)BinaryComparable.getBytes()方法进行分区。
void|setConf(Configuration conf)|设置此对象使用的配置。
static void|setLeftOffset(Configuration conf, int offset)|使用Python语法bytes[offset:]设置子数组用来进行分区。
static void|setRightOffset(Configuration conf, int offset)|使用Python语法bytes[:(offset+1)]设置子数组用来进行分区。
static void|setOffsets(Configuration conf, int left, int right)|使用Python语法bytes[left:(right+1)]设置子数组用来进行分区。

主要看一下getPartition方法:
```java
public int getPartition(BinaryComparable key, V value, int numPartitions) {
  int length = key.getLength();
  int leftIndex = (leftOffset + length) % length;
  int rightIndex = (rightOffset + length) % length;
  int hash = WritableComparator.hashBytes(key.getBytes(),
    leftIndex, rightIndex - leftIndex + 1);
  return (hash & Integer.MAX_VALUE) % numPartitions;
}
```
对BinaryComparable类型的键值进行分区，用到BinaryComparable的两个方法:key.getLength方法获取byte数组长度，key.getBytes方法获取byte数组。最后通过`WritableComparator.hashBytes`的`hashBytes方法`对子数组进行哈希:
```java
public static int hashBytes(byte[] bytes, int offset, int length) {
  int hash = 1;
  for(int i = offset; i < offset + length; ++i) {
    hash = 31 * hash + bytes[i];
  }
  return hash;
}
```

#### 2.4 源码

```java
@InterfaceAudience.Public
@InterfaceStability.Evolving
public class BinaryPartitioner<V> extends Partitioner<BinaryComparable, V> implements Configurable {

  public static final String LEFT_OFFSET_PROPERTY_NAME =
    "mapreduce.partition.binarypartitioner.left.offset";
  public static final String RIGHT_OFFSET_PROPERTY_NAME =
    "mapreduce.partition.binarypartitioner.right.offset";

  /**
   * Set the subarray to be used for partitioning to
   * <code>bytes[left:(right+1)]</code> in Python syntax.
   *
   * @param conf configuration object
   * @param left left Python-style offset
   * @param right right Python-style offset
   */
  public static void setOffsets(Configuration conf, int left, int right) {
    conf.setInt(LEFT_OFFSET_PROPERTY_NAME, left);
    conf.setInt(RIGHT_OFFSET_PROPERTY_NAME, right);
  }

  /**
   * Set the subarray to be used for partitioning to
   * <code>bytes[offset:]</code> in Python syntax.
   *
   * @param conf configuration object
   * @param offset left Python-style offset
   */
  public static void setLeftOffset(Configuration conf, int offset) {
    conf.setInt(LEFT_OFFSET_PROPERTY_NAME, offset);
  }

  /**
   * Set the subarray to be used for partitioning to
   * <code>bytes[:(offset+1)]</code> in Python syntax.
   *
   * @param conf configuration object
   * @param offset right Python-style offset
   */
  public static void setRightOffset(Configuration conf, int offset) {
    conf.setInt(RIGHT_OFFSET_PROPERTY_NAME, offset);
  }

  private Configuration conf;
  private int leftOffset, rightOffset;

  public void setConf(Configuration conf) {
    this.conf = conf;
    leftOffset = conf.getInt(LEFT_OFFSET_PROPERTY_NAME, 0);
    rightOffset = conf.getInt(RIGHT_OFFSET_PROPERTY_NAME, -1);
  }

  public Configuration getConf() {
    return conf;
  }

  /**
   * Use (the specified slice of the array returned by)
   * {@link BinaryComparable#getBytes()} to partition.
   */
  @Override
  public int getPartition(BinaryComparable key, V value, int numPartitions) {
    int length = key.getLength();
    int leftIndex = (leftOffset + length) % length;
    int rightIndex = (rightOffset + length) % length;
    int hash = WritableComparator.hashBytes(key.getBytes(),
      leftIndex, rightIndex - leftIndex + 1);
    return (hash & Integer.MAX_VALUE) % numPartitions;
  }

}
```

### 3. KeyFieldBasedPartitioner

KeyFieldBasedPartitioner<k2, v2>也是基于hash的Partitioner。和BinaryPatitioner不同的是，它提供了多个区间用于计算哈希。当区间数为0时KeyFieldBasedPartitioner退化成HashPartitioner。

```java
package org.apache.hadoop.mapreduce.lib.partition;
...
@InterfaceAudience.Public
@InterfaceStability.Stable
public class KeyFieldBasedPartitioner<K2, V2> extends Partitioner<K2, V2>
    implements Configurable {

  private static final Log LOG = LogFactory.getLog(
                                   KeyFieldBasedPartitioner.class.getName());
  public static String PARTITIONER_OPTIONS =
    "mapreduce.partition.keypartitioner.options";
  private int numOfPartitionFields;

  private KeyFieldHelper keyFieldHelper = new KeyFieldHelper();

  private Configuration conf;

  public void setConf(Configuration conf) {
    this.conf = conf;
    keyFieldHelper = new KeyFieldHelper();
    String keyFieldSeparator =
      conf.get(MRJobConfig.MAP_OUTPUT_KEY_FIELD_SEPERATOR, "\t");
    keyFieldHelper.setKeyFieldSeparator(keyFieldSeparator);
    if (conf.get("num.key.fields.for.partition") != null) {
      LOG.warn("Using deprecated num.key.fields.for.partition. " +
      		"Use mapreduce.partition.keypartitioner.options instead");
      this.numOfPartitionFields = conf.getInt("num.key.fields.for.partition",0);
      keyFieldHelper.setKeyFieldSpec(1,numOfPartitionFields);
    } else {
      String option = conf.get(PARTITIONER_OPTIONS);
      keyFieldHelper.parseOption(option);
    }
  }

  public Configuration getConf() {
    return conf;
  }

  public int getPartition(K2 key, V2 value, int numReduceTasks) {
    byte[] keyBytes;

    List <KeyDescription> allKeySpecs = keyFieldHelper.keySpecs();
    if (allKeySpecs.size() == 0) {
      return getPartition(key.toString().hashCode(), numReduceTasks);
    }

    try {
      keyBytes = key.toString().getBytes("UTF-8");
    } catch (UnsupportedEncodingException e) {
      throw new RuntimeException("The current system does not " +
          "support UTF-8 encoding!", e);
    }
    // return 0 if the key is empty
    if (keyBytes.length == 0) {
      return 0;
    }

    int []lengthIndicesFirst = keyFieldHelper.getWordLengths(keyBytes, 0,
        keyBytes.length);
    int currentHash = 0;
    for (KeyDescription keySpec : allKeySpecs) {
      int startChar = keyFieldHelper.getStartOffset(keyBytes, 0,
        keyBytes.length, lengthIndicesFirst, keySpec);
       // no key found! continue
      if (startChar < 0) {
        continue;
      }
      int endChar = keyFieldHelper.getEndOffset(keyBytes, 0, keyBytes.length,
          lengthIndicesFirst, keySpec);
      currentHash = hashCode(keyBytes, startChar, endChar,
          currentHash);
    }
    return getPartition(currentHash, numReduceTasks);
  }

  protected int hashCode(byte[] b, int start, int end, int currentHash) {
    for (int i = start; i <= end; i++) {
      currentHash = 31*currentHash + b[i];
    }
    return currentHash;
  }

  protected int getPartition(int hash, int numReduceTasks) {
    return (hash & Integer.MAX_VALUE) % numReduceTasks;
  }

  public void setKeyFieldPartitionerOptions(Job job, String keySpec) {
    job.getConfiguration().set(PARTITIONER_OPTIONS, keySpec);
  }

  public String getKeyFieldPartitionerOption(JobContext job) {
    return job.getConfiguration().get(PARTITIONER_OPTIONS);
  }
}

```
