
## 1. 元数据定义

### 1.1  CSV 文件

要想将 CSV 集成到 Calcite 当中，首先要让 Calcite 能够识别这些文件，但是 Calcite 并不知道这些文件是什么，需要因此对 CSV 文件的格式进行定义。CSV 文件的第一行是元数据信息，采用 `FieldName1:FieldType,FieldNameN:FieldType` 的格式存储，跟 Excel 中的表头信息比较类似，通过这种方式告诉了 Calcite 文件的字段名称和字段类型。如下是 `sales.csv` 的示例：
```
DEPTNO:int,NAME:string
10,"Sales"
20,"Marketing"
30,"Accounts"
```

### 1.2 配置文件

有了 CSV 文件之后，我们需要定义一个 `model` 配置文件，如下是一个示例：
```json
{
  "version": "1.0",
  "defaultSchema": "SALES",
  "schemas": [
    {
      "name": "SALES",
      "type": "custom",
      "factory": "com.calcite.example.adapter.csv.CsvSchemaFactory",
      "operand": {
        "directory": "sales"
      }
    }
  ]
}
```
在分析 model 配置文件之前，先了解几个重要的概念：
- `Schema`：是 Table 和 Function 的名称空间，是一个可嵌套的结构。Schema 还可以有 subSchema，理论上可以无限嵌套。Schema 可以理解成传统关系型数据库中的 `Database`，`Database` 下面还有 Table。在 Calcite 中，顶层的 Schema 是 root，自定义的 Schema 是 root 的 subSchema，同时还可以设置 defaultSchema，类似传统关系型数据库中的默认数据库。
- `Table`：就是数据库中的表。在 Table 中描述了字段名以及相应的类型、表的统计信息，例如表有多少条记录等等，这里先不展开讲。

默认情况下，数据模型的配置文件使用 JSON 文件格式存储的。再来看这份 model 文件，就比较清晰了。配置文件描述了多少个 Schema、每个 Schema 是如何创建的以及默认的 Schema 是什么：
- defaultSchema 属性设置默认 Schema。
- schemas 是数组类型，每一项代表一个 Schema 描述信息
  - name：定义了 Schema 的名称，在这命名为 `SALES`。
  - type：由于类型是我们自己定义的，因此类型为 `custom`。
  - factory：表示创建 Schema 的工厂类，在这设置 CSV 文件的 Schema 工厂类路径为 `com.calcite.example.adapter.csv.SimpleCsvSchemaFactory`。

这样 Calcite 就可以知道这些 CSV 文件长什么样子，要用什么方式去调用、解析。

## 2. 搭建

要实现只有全表扫描功能的简单数据库来查询 CSV 文件需要做如下几步：
- 引入 POM 依赖
- 自定义实现 SchemaFactory
- 自定义实现 Schema
- 自定义实现 Table
- 自定义实现 Enumerator

### 2.1 引入 POM 依赖

需要引入如下坐标依赖：
```xml
<!-- calcite -->
<dependency>
    <groupId>org.apache.calcite</groupId>
    <artifactId>calcite-core</artifactId>
    <version>1.32.0</version>
</dependency>
```

### 2.2 自定义实现 SchemaFactory

在上述文件中指定的包路径下去编写 SimpleCsvSchemaFactory 类，实现 SchemaFactory 接口。核心要实现接口中的唯一方法 create 来创建 Schema：
```java
public class SimpleCsvSchemaFactory implements SchemaFactory {
    // 单例模式
    public static final SimpleCsvSchemaFactory INSTANCE = new SimpleCsvSchemaFactory();
    private SimpleCsvSchemaFactory() {
    }
    @Override
    public Schema create(SchemaPlus parentSchema, String name, Map<String, Object> operand) {
        final String directory = (String) operand.get("directory");
        // CSV 文件
        final File base = (File) operand.get(ModelHandler.ExtraOperand.BASE_DIRECTORY.camelName);
        File directoryFile = new File(directory);
        if (base != null && !directoryFile.isAbsolute()) {
            directoryFile = new File(base, directory);
        }
        // 创建 CsvSchema
        return new SimpleCsvSchema(directoryFile);
    }
}
```
create 参数说明如下：
- parentSchema：它的父节点，一般为root
- name：schema 的名字，在 model 中定义的
- operand：传入的自定义参数，也是在 mode 中定义的，是一个 Map 类型

从上面可以知道 operand 中自自定义了一个参数 directory，即读取 CSV 文件的根目录。SimpleCsvSchemaFactory 通过这个目录创建一个 `SimpleCsvSchema` 对象。构造
Schema 的目的就是创建一个数据库，包含一些表的元数据信息。

## 2. 自定义实现 Schema

实现 SchemaFactory 接口之后就需要实现自定义 Schema 类。自定义的 Schema 类需要实现 Schema 接口，但是直接实现 Schema 接口需要实现的方法太多。官方的 AbstractSchema 类帮我们实现了一部分，这样就只需要继承 AbstractSchema 类实现 getTableMap 方法就行，当然如果有其他定制化需求可以直接实现 Schema 接口：
```java
public class SimpleCsvSchema extends AbstractSchema {
    private final File directoryFile;

    public SimpleCsvSchema(File directoryFile) {
        super();
        this.directoryFile = directoryFile;
    }

    @Override
    protected Map<String, Table> getTableMap() {
        ...
    }
}
```
核心的逻辑就是 getTableMap 方法，用于创建出 Table 表。它会扫描 Resource 下面的所有以 `.csv` 结尾的文件，将每个 csv 文件映射成 Table 对象，最终以 map 形式返回(其中键为 csv 文件路径，值为 Table 对象)：
```java
protected Map<String, Table> getTableMap() {
    // 寻找指定目录下以 .csv 结尾的文件
    final Source baseSource = Sources.of(directoryFile);
    File[] files = directoryFile.listFiles((dir, name) -> {
        return name.endsWith(".csv");
    });
    if (files == null) {
        System.out.println("directory " + directoryFile + " not found");
        files = new File[0];
    }
    // 文件与 Table 映射
    final ImmutableMap.Builder<String, Table> builder = ImmutableMap.builder();
    for (File file : files) {
        Source source = Sources.of(file);
        final Source csvSource = source.trimOrNull(".csv");
        if (csvSource == null) {
            continue;
        }
        // 根据文件创建对应的 Table
        final Table table = new SimpleCsvTable(source, null);
        builder.put(csvSource.relative(baseSource).path(), table);
    }
    return builder.build();
}
```
通过上面可以知道 CSVSchema 的实现也比较简单，遍历读取根目录下的每个 CSV 文件创建成 Table。

## 3. 自定义实现 Table

从上面可以知道 Schema 会将每个 csv 文件映射成 Table 对象，即一个 csv 文件对应一个 Table。接下来我们去自定义实现一个 SimpleCsvTable，看看是如何将一个 CSV 文件映射为一个 Table 对象。自定义 Table 是本文中最复杂的，如下图所示：

![](1)

我们自定义实现的 SimpleCsvTable 继承了 AbstractTable 抽象类以及实现了 ScannableTable 接口：
```java
public class SimpleCsvTable extends AbstractTable implements ScannableTable {
    @Override
    public RelDataType getRowType(RelDataTypeFactory relDataTypeFactory) {
        // 定义Table的字段以及字段类型
        return null;
    }

    @Override
    public Enumerable<@Nullable Object[]> scan(DataContext root) {
        // 如何遍历读取CSV文件 全表扫描
        return null;
    }
}
```
SimpleCsvTable 继承 AbstractTable 抽象类，作用是定义 Table 的字段以及字段类型；实现 ScannableTable 接口是如何实现遍历读取 CSV 文件的数据。Table 接口有如下三个方法：
```java
RelDataType getRowType(RelDataTypeFactory var1);
Statistic getStatistic();
TableType getJdbcTableType();
```
AbstractTable 默认已经帮我们实现了 getStatistic 和 getJdbcTableType，所以我们只需要实现 getRowType 方法即可。

### 3.1 定义字段类型和名称

先获取数据类型和名称，即单表结构，从 csv 文件头中获取（当前文件头需要我们自己定义，包括规则我们也可以定制化）。
```java
public RelDataType getRowType(RelDataTypeFactory typeFactory) {
    if (protoRowType != null) {
        return protoRowType.apply(typeFactory);
    }
    if (rowType == null) {
        rowType = SimpleCsvEnumerator.deduceRowType((JavaTypeFactory) typeFactory, source, null);
    }
    return rowType;
}
```

### 3.2 定义如何读取 Csv 文件

```java
public Enumerable<@Nullable Object[]> scan(DataContext root) {
    JavaTypeFactory typeFactory = root.getTypeFactory();
    // 字段类型
    List<RelDataType> fieldTypes = new ArrayList<>();
    SimpleCsvEnumerator.deduceRowType(typeFactory, source, fieldTypes);
    // 字段？
    List<Integer> fields = ImmutableIntList.identity(fieldTypes.size());

    final AtomicBoolean cancelFlag = DataContext.Variable.CANCEL_FLAG.get(root);
    return new AbstractEnumerable<@Nullable Object[]>() {
        @Override
        public Enumerator<@Nullable Object[]> enumerator() {
            return new SimpleCsvEnumerator<>(source, cancelFlag, fieldTypes, fields);
        }
    };
}
```

实现读取 CSV 的逻辑

Enumerator 是 Linq 风格的迭代器，它有4个方法：
```java
public interface Enumerator<T> extends AutoCloseable {
    T current();
    boolean moveNext();
    void reset();
    void close();
}
```
`current` 返回游标所指的当前记录，需要注意的是 `current` 并不会改变游标的位置，这一点和 iterator 是不同的，在 iterator 相对应的是 next 方法，每一次调用都会将游标移动到下一条记录，current 则不会，Enumerator 是在调用 moveNext 方法时才会移动游标。moveNext 方法将游标指向下一条记录，并获取当前记录供 current 方法调用，如果没有下一条记录则返回false。




。。。。
