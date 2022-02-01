

[KIP-66](https://cwiki.apache.org/confluence/display/KAFKA/KIP-66%3A+Single+Message+Transforms+for+Kafka+Connect) 是在 Apache Kafka 0.10.2 中添加的，并带来了 Single Message Transforms (SMT) 的新功能。使用 SMT，你可以修改通过 Kafka Connect 管道的数据，而不需要额外的流处理器。你可以修改字段、修改 Topic 名称、有条件地删除消息等，SMT 是一个完美的解决方案。如果你遇到了聚合、流 Join 等问题，那么 SMT 可能不是最好的选择，你可以考虑一下 Kafka Streams 或 KsqlDB。

Kafka Connect 包含了如下一些广泛适用的数据和路由 Transform:
- Cast：
- InsertField：使用静态数据或者记录的元数据来添加一个字段
- ReplaceField：过滤或者重命名字段
- MaskField：对0，空字符串等用有效的 NULL 值替换、对非空字符串或数字值用自定义的替换
- ExtractField：



## 1. Cast

Cast Single Message Transform 用来实现数据类型转换，可以让你改变 Kafka 消息中字段的数据类型，支持数字、字符串和布尔值。Cast 接受一个参数，其中列出要转换的字段以及目标数据类型。通过用逗号分隔每，可以指定多个字段。

### 1.1 用法

Cast 需要配置三个字段：
- transforms：Transform 的名字，用来配置该 Transform 的其他属性（其他属性的配置依赖该字段）。
- transforms.xxx.type：Transform 的类型，如果对记录的 Key 进行操作，需要指定为 org.apache.kafka.connect.transforms.Cast$Key，如果
如果对记录的 Value 进行操作，需要指定为 org.apache.kafka.connect.transforms.Cast$Value。
- transforms.xxx.spec：需要转换的字段以及目标数据类型。如果原生类型可以转换整个值，对于像 Map 和 Structs 的复杂类型，设置为以逗号分隔的字段名和强制转换的类型，格式为 field1:type1,field2:type2。可以支持的类型有 int8, int16, int32, int64, float32, float64, boolean和 string。

### 1.2 示例

Cast 可以转换整个原生类型键/值以及复杂类型(例如，Struct 或 Map)键或值的一个或多个字段。下面的两个配置片段示例展示了如何在这两个场景中使用Cast。

#### 1.2.1 原生类型转换

如下示例展示了如何使用 Cast 将64位浮点数的 Value 转换为字符串类型：
```
"transforms": "Cast",
"transforms.Cast.type": "org.apache.kafka.connect.transforms.Cast$Value",
"transforms.Cast.spec": "string"
```
Before: 63521704.02
After: "63521704.02"

#### 1.2.2 复杂类型转换

如下例子展示了如何对一个复杂类型的键或值使用 Cast。spec 参数指定了以逗号分隔的 `field:type` 键值对，其中 field 是要进行类型转换的字段名称，type 是要转换的目标类型：
```
"transforms": "Cast",
"transforms.Cast.type": "org.apache.kafka.connect.transforms.Cast$Value",
"transforms.Cast.spec": "ID:string,score:float64"
```
假设应用 Transform 之前的消息 Value 如下所示：
```json
{"ID": 46920,"score": 4761}
```
转换之后消息 Value 如下所示，ID 字段转为 String 类型，score 字段转换为 float64 类型：
```json
{"ID": "46290","score": 4761.0}
```

## 2. InsertField

InsertField Single Message Transform 可以将静态字段值或者记录元数据属性（Kafka Topic 名称、分区以及消息被读取的偏移量）添加到 Kafka Connect 发送到 Sink 的消息中。

#### 2.1 用法

InsertField 需要配置三个字段：
- transforms：Transform 的名字，用来配置该 Transform 的其他属性（其他属性的配置依赖该字段）。
- transforms.xxx.type：Transform 的类型，如果对记录的 Key 进行操作，需要指定为 org.apache.kafka.connect.transforms.InsertField$Key，如果
如果对记录的 Value 进行操作，需要指定为 org.apache.kafka.connect.transforms.InsertField$Value。
- transforms.xxx.static.field：

#### 2.2



。。。
