



Table Schema 定义了列的名称和类型，类似于 SQL 中 CREATE TABLE 语句的列定义。此外，可以指定列与 Table 数据编码 Format 的字段进行映射。如果列的名称与输入/输出格式中的不同，那么字段的来源就比较重要了。例如，列 user_name 引用 JSON 格式的 `$$-user-name` 字段。此外，schema 还需要将外部系统的类型映射为 Flink 支持的类型。在 Table Sink 使用场景下，只有具有有效 Schema 的数据才被写入外部系统。

如下示例展示了一个简单的 Schema：没有时间属性，输入/输出到 Table 列一一映射：
```java
.withSchema(
  new Schema()
    .field("MyField1", Types.INT)
    .field("MyField2", Types.STRING)
    .field("MyField3", Types.BOOLEAN)
)
```
对于每个字段，除了列的名称和类型之外，还可以声明如下属性：
```java
.withSchema(
  new Schema()
    .field("MyField1", Types.SQL_TIMESTAMP)
      .proctime()      // 可选: 声明该字段为 processing-time 时间属性
    .field("MyField2", Types.SQL_TIMESTAMP)
      .rowtime(...)    // 可选: 声明该字段为 event-time 时间属性
    .field("MyField3", Types.BOOLEAN)
      .from("mf3")     // 可选: 该字段引用(或者重命名)的原始输入字段
)
```
使用无界流 Table 时，时间属性是必不可少的。因此，处理时间 processing-time 和事件时间 event-time 属性都可以定义为 Schema 的一部分。

## 2. Rowtime 属性

为了控制 Table 的事件时间行为，Flink 提供了预定义的时间戳提取器和水印策略。

支持以下时间戳提取器：


## 3. Update 模式

```java
.connect(...)
  .inAppendMode()    // otherwise: inUpsertMode() or inRetractMode()
```





。。。
