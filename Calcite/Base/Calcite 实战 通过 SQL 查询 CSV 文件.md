
```
<!-- calcite -->
<dependency>
    <groupId>org.apache.calcite</groupId>
    <artifactId>calcite-core</artifactId>
    <version>1.32.0</version>
</dependency>
```

自定义实现 SchemaFactory
自定义实现 Schema
自定义实现 Table
自定义实现 Enumerator
决定Table的字段类型
使用ScannableTable实现简单的全表扫描

## 1. 自定义实现 SchemaFactory

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
        // 每个文件对应一个 Table
        final Table table = new SimpleCsvTable(source, null);
        builder.put(csvSource.relative(baseSource).path(), table);
    }
    return builder.build();
}
```

## 3. 自定义实现 Table

从上面可以知道 Schema 会将每个 csv 文件映射成 Table 对象，即一个 csv 文件对应一个 Table。接下来我们去自定义 Table，自定义 Table 可以实现 Table 接口，也可以继承自 AbstractTable 类。在这里我们实现功能比较简单，可以直接继承自 AbstractTable 类：
```java
public class SimpleCsvTable extends AbstractTable {
    @Override
    public RelDataType getRowType(RelDataTypeFactory relDataTypeFactory) {
        return null;
    }
}
```
自定义实现 Table 的核心是我们要定义字段的类型和名称，以及如何读取 csv 文件。

### 3.1 定义字段类型和名称

先获取数据类型和名称，即单表结构，从csv文件头中获取（当前文件头需要我们自己定义，包括规则我们也可以定制化）。
```java

```

### 3.2 定义如何读取 Csv 文件







。。。。
