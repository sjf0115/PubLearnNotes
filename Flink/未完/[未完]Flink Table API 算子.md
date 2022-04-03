
Table API 支持如下操作。但需要注意的是，并非所有操作都可以在批处理和流式处理场景下使用。

## 1. Scan, Projection, and Filter

### 1.1 From

> 适用于 Batch & Streaming 场景

类似于 SQL 查询中的 FROM 子句。对注册表进行扫描：
```java
Table orders = tableEnv.from("Orders");
```

### 1.2 FromValues

> 适用于 Batch & Streaming 场景

类似于 SQL 查询中的 VALUES 子句。根据提供的 Row 生成一个内联表。你可以使用 row(...) 表达式来创建复合 Row：
```java
Table table = tEnv.fromValues(
   row(1, "ABC"),
   row(2L, "ABCDE")
);
```
上面代码会产生一个具有如下 Schema 的表 Table：
```
root
|-- f0: BIGINT NOT NULL     // 原始 INT 和 BIGINT 类型生成 BIGINT 类型
|-- f1: VARCHAR(5) NOT NULL // 原始 CHAR(3) 和 CHAR(5) 类型生成 VARCHAR(5) 类型
```
上述方法会根据输入表达式自动进行类型推断。如果有一个位置的类型与其他不同，该方法尝试为所有类型找到一个共同的超类型。如果不存在公共超类型，则会抛出异常。

除了上述方法还可以显式指定请求的类型：
```java
Table table = tEnv.fromValues(
    DataTypes.ROW(
        DataTypes.FIELD("id", DataTypes.DECIMAL(10, 2)),
        DataTypes.FIELD("name", DataTypes.STRING())
    ),
    row(1, "ABC"),
    row(2L, "ABCDE")
);
```
上述方法会生成具有如下 Schema 的表 Table：
```
root
|-- id: DECIMAL(10, 2)
|-- name: STRING
```

### 1.3 Select

> 适用于 Batch & Streaming 场景

类似于 SQL SELECT 语句。执行选择操作：
```java
Table orders = tableEnv.from("Orders");
Table result = orders.select($("a"), $("c").as("d"));
```
您可以使用星号 `*` 作为通配符，选择表 Table 中的所有列：
```java
Table result = orders.select($("*"));
```

### 1.4 As

重命名字段：
```java
Table orders = tableEnv.from("Orders");
Table result = orders.as("x, y, z, t");
```

### 1.5 Where / Filter

类似于 SQL WHERE 子句。过滤掉不需要的 Row：
```java
Table orders = tableEnv.from("Orders");
Table result = orders.where($("b").isEqual("red"));
```
或者：
```java
Table orders = tableEnv.from("Orders");
Table result = orders.filter($("b").isEqual("red"));
```

## 2. 列操作

### 2.1 AddColumns

添加字段。如果添加的字段已经存在，则抛出异常：
```java
Table orders = tableEnv.from("Orders");
Table result = orders.addColumns(concat($("c"), "sunny"));
```

### 2.2 AddOrReplaceColumns

添加字段。如果添加的列名与现有列名相同，则现有字段被替换。此外，如果添加的字段具有重复的字段名称，则使用最后一个：
```java
Table orders = tableEnv.from("Orders");
Table result = orders.addOrReplaceColumns(concat($("c"), "sunny").as("desc"));
```

### 2.3 DropColumns

删除字段：
```java
Table orders = tableEnv.from("Orders");
Table result = orders.dropColumns($("b"), $("c"));
```

### 2.4 RenameColumns

对字段重命名。字段表达式是别名表达式，并且只能重命名现有字段。
```java
Table orders = tableEnv.from("Orders");
Table result = orders.renameColumns($("b").as("b2"), $("c").as("c2"));
```

## 3. 聚合操作

### 3.1 GroupBy

类似于 SQL GROUP BY 子句。使用如下聚合算子对分组 Key 上的 Row 进行分组。
```java
Table orders = tableEnv.from("Orders");
Table result = orders.groupBy($("a")).select($("a"), $("b").sum().as("d"));
```

### 3.2 GroupBy Window

在分组窗口上对表 Table 进行分组和聚合。
```java
Table orders = tableEnv.from("Orders");
Table result = orders
    .window(Tumble.over(lit(5).minutes()).on($("rowtime")).as("w")) // define window
    .groupBy($("a"), $("w")) // group by key and window
    // access window properties and aggregate
    .select(
        $("a"),
        $("w").start(),
        $("w").end(),
        $("w").rowtime(),
        $("b").sum().as("d")
    );
```

### 3.3 Over Window

类似于 SQL OVER 子句。基于前面和后面行的窗口（范围）为每一行计算窗口聚合。
```java
Table orders = tableEnv.from("Orders");
Table result = orders
    // define window
    .window(
        Over
          .partitionBy($("a"))
          .orderBy($("rowtime"))
          .preceding(UNBOUNDED_RANGE)
          .following(CURRENT_RANGE)
          .as("w"))
    // sliding aggregate
    .select(
        $("a"),
        $("b").avg().over($("w")),
        $("b").max().over($("w")),
        $("b").min().over($("w"))
    );
```




[](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/table/tableapi/#operations)
