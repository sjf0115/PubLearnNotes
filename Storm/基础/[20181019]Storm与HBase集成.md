### 1. 用法

与HBase交互的主要API是`org.apache.storm.hbase.bolt.mapper.HBaseMapper`接口：
```java
public interface HBaseMapper extends Serializable {
    byte[] rowKey(Tuple tuple);
    ColumnList columns(Tuple tuple);
}
```
`rowKey()`方法比较简单：给定一个Storm元组(tuple)，返回一个表示行键的字节数组。`columns()`方法定义了写入HBase行中的内容。`ColumnList`类中允许你添加HBase标准列和HBase计数器列。

添加标准列，使用`addColumn()`方法：
```java
ColumnList cols = new ColumnList();
cols.addColumn(this.columnFamily, field.getBytes(), toBytes(tuple.getValueByField(field)));
```
要添加计数器列，使用`addCounter()`方法：
```java
ColumnList cols = new ColumnList();
cols.addCounter(this.columnFamily, field.getBytes(), toLong(tuple.getValueByField(field)));
```
当远程HBase启用安全性时，需要为storm-hbase连接器提供kerberos密钥表和相应的主体名称。 具体来说，传递到拓扑中的Config对象应包含{（“storm.keytab.file”，“$ keytab”），（“storm.kerberos.principal”，“$ principal”）}。 例：



> Storm版本：1.1.0

原文：http://storm.apachecn.org/releases/cn/1.1.0/storm-hbase.html
