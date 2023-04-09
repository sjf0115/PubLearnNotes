这是一个分步骤的教程，展示了如何构建并与 Calcite 进行连接。通过一个简单的适配器可以使 CSV 文件看起来像是一个包含表的模式 Schema。Calcite 则完成剩下的工作，并提供完整的 SQL 接口。

Calcite-example-CSV 是一个功能齐全的 Calcite 适配器，可以读取 CSV 格式的文本文件。需要注意的是，几百行 Java 代码就足以提供完整的 SQL 查询功能。CSV 也可以用来构建其他数据格式适配器的模板。虽然代码行数不多，但是有几个重要的概念需要了解一下：
- 使用 SchemaFactory 和 Schema 接口的用户自定义模式(Schema)；
- 在 JSON 格式的模型文件中声明模式；
- 在 JSON 格式的模型文件中声明视图；
- 使用 Table 接口的用户自定义表；
- 确定表的记录类型；
- Table 接口的简单实现：使用 ScannableTable 接口直接枚举所有行；
- Table 接口的更高级实现：使用 FilterableTable 接口可以根据简单的谓词过滤行；
- Table 接口的更高级实现：使用 TranslatableTable 接口利用计划器规则转换为关系运算符。

## 1. 下载和构建

你需要版本为 8、9 或 10 的 Java 以及 Git：
```
$ git clone https://github.com/apache/calcite.git
$ cd calcite/example/csv
$ ./sqlline
```

## 2. 首次查询

现在让我们使用 sqlline 连接到 Calcite，sqlline 是一个包含在 Calcite 项目中的 SQL shell 功能。
```
$ ./sqlline
sqlline> !connect jdbc:calcite:model=src/test/resources/model.json admin admin
```
如果你运行的是 Windows，则命令为 sqlline.bat。

执行一个元数据查询：


## 3. 模式发现

那么，Calcite 是如何发现这些表的呢？记住，Calcite 内核对 CSV 文件一无所知（作为一个没有存储层的数据库，Calcite 不了解任何文件格式）。Calcite 知道这些表，完全是因为我们告诉它去执行 calcite-example-csv 项目中的代码。

发现过程包含了几个步骤。首先，我们基于模型文件中的模式工厂类定义了一个模式。然后，模式工厂创建了一个模式，并且这个模式创建一些表，每个表都知道通过扫描 CSV 文件来获取数据。最后，在 Calcite 解析完查询并生成使用这些表的执行计划后，Calcite 会在执行查询时，调用这些表来读取数据。现在让我们更详细地了解这些步骤。

在 JDBC 连接字符串上，我们以 JSON 格式给出了模型的路径。下面是模型的内容：
```json
{
    "version": "1.0",
    "defaultSchema": "SALES",
    "schemas": [
        {
            "name": "SALES",
            "type": "custom",
            "factory": "org.apache.calcite.adapter.csv.CsvSchemaFactory",
            "operand": {
                "directory": "sales"
            }
        }
    ]
}
```
该模型定义了一个名为 'SALES' 的单模式。该模式由插件类 `org.apache.calcite.adapter.csv.CsvSchemaFactory` 提供支持。它是 Calcite -example-csv 项目的一部分，实现了 Calcite 的 SchemaFactory 接口。CsvSchemaFactory 的 create 方法通过从模型文件中传入 directory 参数并实例化一个模式:
```java
public Schema create(SchemaPlus parentSchema, String name, Map<String, Object> operand) {
  final String directory = (String) operand.get("directory");
  final File base = (File) operand.get(ModelHandler.ExtraOperand.BASE_DIRECTORY.camelName);
  File directoryFile = new File(directory);
  if (base != null && !directoryFile.isAbsolute()) {
    directoryFile = new File(base, directory);
  }
  String flavorName = (String) operand.get("flavor");
  CsvTable.Flavor flavor;
  if (flavorName == null) {
    flavor = CsvTable.Flavor.SCANNABLE;
  } else {
    flavor = CsvTable.Flavor.valueOf(flavorName.toUpperCase(Locale.ROOT));
  }
  return new CsvSchema(directoryFile, flavor);
}
```


在模型的驱动下，Schema 工厂实例化了一个名为 'SALES' 的 Schema。该 Schema 是 `org.apache.calcite.adapter.csv.CsvSchema` 的一个实例，并实现了 Calcite 的 Schema 接口。

Schema 的任务是生成一个表列表。(它还可以列出子 Schema和表函数，但这些都是高级功能，而 calcite-example-csv 并没有实现)这些表实现了 Calcite 的 Table 接口。CsvSchema 生成的表是 CsvTable 及其子类的实例。

下面是 CsvSchema 的相关代码，重写了 AbstractSchema 基类中的 getTableMap() 方法：
```java

```
Schema 扫描目录，找到想要扩展名的所有文件，并为它们创建表。在本例中，目录为 sales，包含了 EMPS.csv.gz、DEPTS.csv 和 SDEPTS.csv 三个文件，分别应了 EMPS、DEPTS 和 SDEPTS 表。

## 4. Schema 中的表和视图

需要注意的是我们不需要在模型中定义表，Schema 会自动生成这些表。除了自动创建的表之外，你还可以使用 schema 中的 tables 属性来定义其他的表。现在我们一起看看如何创建视图，一个重要且有用的表类型。视图看起来就像你写的一个查询中的表。但它不存储数据，只是通过执行查询来获取结果。当为查询语句生成查询计划时，视图会被扩展，因此查询计划器通常可以执行优化，例如删除那些在最终结果中未使用的 SELECT 子句表达式。如下所示是一个定义视图的 schema：
```json
{
  version: '1.0',
  defaultSchema: 'SALES',
  schemas: [
    {
      name: 'SALES',
      type: 'custom',
      factory: 'org.apache.calcite.adapter.csv.CsvSchemaFactory',
      operand: {
        directory: 'sales'
      },
      tables: [
        {
          name: 'FEMALE_EMPS',
          type: 'view',
          sql: 'SELECT * FROM emps WHERE gender = \'F\''
        }
      ]
    }
  ]
}
```
`"type": "view"` 这一行将 `FEMALE_EMPS` 标记为一个视图，而不是一个常规表或自定义表。需要注意的是，视图定义中的单引号使用反斜杠进行转义，这是 JSON 的正常用法。JSON 不容易编写长字符串，因此 Calcite 支持另一种语法。如果你的视图中有一个很长的 SQL 语句，你可以将单个字符串模式改为多行列表模式：
```json
{
  name: 'FEMALE_EMPS',
  type: 'view',
  sql: [
    'SELECT * FROM emps',
    'WHERE gender = \'F\''
  ]
}
```
现在我们定义了一个视图，可以在查询中直接使用它，就像使用表一样：
```sql
sqlline> SELECT e.name, d.name FROM female_emps AS e JOIN depts AS d on e.deptno = d.deptno;
+--------+------------+
|  NAME  |    NAME    |
+--------+------------+
| Wilma  | Marketing  |
+--------+------------+
```

## 5. 自定义表

自定义表是那些由用户自定义代码驱动的表。他们不需要存在于自定义 Schema 中。如下所示是一个 model-with-custom-table.json 模型文件的示例，其中定义了一个自定义表：
```json
{
  version: '1.0',
  defaultSchema: 'CUSTOM_TABLE',
  schemas: [
    {
      name: 'CUSTOM_TABLE',
      tables: [
        {
          name: 'EMPS',
          type: 'custom',
          factory: 'org.apache.calcite.adapter.csv.CsvTableFactory',
          operand: {
            file: 'sales/EMPS.csv.gz',
            flavor: "scannable"
          }
        }
      ]
    }
  ]
}
```
我们可以使用常规的方式查询自定义表：
```
sqlline> !connect jdbc:calcite:model=src/test/resources/model-with-custom-table.json admin admin
sqlline> SELECT empno, name FROM custom_table.emps;
+--------+--------+
| EMPNO  |  NAME  |
+--------+--------+
| 100    | Fred   |
| 110    | Eric   |
| 110    | John   |
| 120    | Wilma  |
| 130    | Alice  |
+--------+--------+
```
该 Schema 是一个常规 Schema，包含一个由 `org.apache.calcite.adapter.csv.CsvTableFactory` 提供支持的自定义表。实现了 Calcite 的 TableFactory 接口。CsvTableFactory 的 create 方法通过从模型文件中传入 file 参数并实例化了一个 CsvScannableTable：
```java
public CsvTable create(SchemaPlus schema, String name, Map<String, Object> operand, @Nullable RelDataType rowType) {
  String fileName = (String) operand.get("file");
  final File base = (File) operand.get(ModelHandler.ExtraOperand.BASE_DIRECTORY.camelName);
  final Source source = Sources.file(base, fileName);
  final RelProtoDataType protoRowType = rowType != null ? RelDataTypeImpl.proto(rowType) : null;
  return new CsvScannableTable(source, protoRowType);
}
```
自定义表实现通常是自定义 Schema 实现的一个更简单方式。这两种方法最终都可能会创建 Table 接口的类似实现，但是对于自定义表，您不需要实现元数据发现。CsvTableFactory 创建了一个 CsvScannableTable，就像 CsvSchema 一样，但是表的实现不会扫描文件系统来查找 `.csv` 文件。自定义表需要模型的开发者做更多的工作，需要明确地指定每个表及其对应文件，但也给开发者更多的控制权限(例如，为每个表提供不同的参数)。

## 6. 模型中的注释

模型可以使用 `/* ... */` 或者 `//` 语法来包含注释：
```json
{
  version: '1.0',
  /* Multi-line
     comment. */
  defaultSchema: 'CUSTOM_TABLE',
  // Single-line comment.
  schemas: [
    ..
  ]
}
```
注释不是标准的 JSON，是一种无害的扩展。

## 7. 使用优化器规则优化查询

到目前为止，我们看到的表实现都表现良好，只要表不包含大量数据。但是，如果你自定义表中有一百列以及一百万行，你肯定更期望系统的每个查询不要检索所有的数据。你可能希望 Calcite 与适配器 adapter 协商，并找到一种更有效的数据访问方式。

这种协商就是查询优化的一种简单形式。Calcite 通过添加优化器规则来支持查询优化。优化器规则通过在查询解析树中查找模式（例如某种表解析树上的投影）来操作，并使用一组新的优化节点来替换树中匹配的节点。

优化器规则像 Scheam 和表一样，也是可扩展的。因此，如果你有一个想要通过 SQL 访问的数据存储，你可以首先定义自定义表或模式 Schema，然后定义一些规则来提高访问的效率。

让我们通过一个实战来加深理解，使用优化器规则访问 CSV 文件中的部分列。让我们对两个非常相似的模式 Schema 运行相同的查询：
```
sqlline> !connect jdbc:calcite:model=src/test/resources/model.json admin admin
sqlline> explain plan for select name from emps;
+-----------------------------------------------------+
| PLAN                                                |
+-----------------------------------------------------+
| EnumerableCalc(expr#0..9=[{inputs}], NAME=[$t1])    |
|   EnumerableTableScan(table=[[SALES, EMPS]])        |
+-----------------------------------------------------+
sqlline> !connect jdbc:calcite:model=src/test/resources/smart.json admin admin
sqlline> explain plan for select name from emps;
+-----------------------------------------------------+
| PLAN                                                |
+-----------------------------------------------------+
| CsvTableScan(table=[[SALES, EMPS]], fields=[[1]])   |
+-----------------------------------------------------+
```
是什么导致了计划上的差异?让我们对比查看一下，发现在 smart.json 模型文件中，只多了一行：
```
flavor: "translatable"
```
这个额外的配置会使用 flavor = TRANSLATABLE 来创建 CsvSchema，它的 createTable 方法会创建 CsvTranslatableTable 而不是之前看过的 CsvScannableTable。CsvTranslatableTable 实现了 TranslatableTable.toRel() 方法来创建 CsvTableScan。表扫描是查询操作树的叶子节点。通常的实现是 EnumerableTableScan，但是我们已经创建了一个独特的子类型，它将导致规则触发。如下所示是完整的规则:
```java
public class CsvProjectTableScanRule
    extends RelRule<CsvProjectTableScanRule.Config> {

  /** Creates a CsvProjectTableScanRule. */
  protected CsvProjectTableScanRule(Config config) {
    super(config);
  }

  @Override public void onMatch(RelOptRuleCall call) {
    final LogicalProject project = call.rel(0);
    final CsvTableScan scan = call.rel(1);
    int[] fields = getProjectFields(project.getProjects());
    if (fields == null) {
      // Project contains expressions more complex than just field references.
      return;
    }
    call.transformTo(
        new CsvTableScan(
            scan.getCluster(),
            scan.getTable(),
            scan.csvTable,
            fields));
  }

  private static int[] getProjectFields(List<RexNode> exps) {
    final int[] fields = new int[exps.size()];
    for (int i = 0; i < exps.size(); i++) {
      final RexNode exp = exps.get(i);
      if (exp instanceof RexInputRef) {
        fields[i] = ((RexInputRef) exp).getIndex();
      } else {
        return null; // not a simple projection
      }
    }
    return fields;
  }

  /** Rule configuration. */
  @Value.Immutable(singleton = false)
  public interface Config extends RelRule.Config {
    Config DEFAULT = ImmutableCsvProjectTableScanRule.Config.builder()
        .withOperandSupplier(b0 ->
            b0.operand(LogicalProject.class).oneInput(b1 ->
                b1.operand(CsvTableScan.class).noInputs()))
        .build();

    @Override default CsvProjectTableScanRule toRule() {
      return new CsvProjectTableScanRule(this);
    }
  }
}
```
规则的默认实例驻留在 CsvRules 的持有类中：
```java
public abstract class CsvRules {
  public static final CsvProjectTableScanRule PROJECT_SCAN =
      CsvProjectTableScanRule.Config.DEFAULT.toRule();
}
```
在默认配置类中（Config 接口中的 DEFAULT 字段），对 withOperandSupplier 方法的调用声明了关系表达式的匹配模式，这个匹配模式会导致规则的触发。如果优化器发现 LogicalProject 的唯一输入是一个没有输入的 CsvTableScan，它将调用这个规则。

规则的变体是可能存在的。例如，不同的规则实例可能会在 CsvTableScan 上匹配到 EnumerableProject。

onMatch 方法生成一个新的关系表达式，并调用 RelOptRuleCall.transformTo() 来表明规则已经成功触发。

## 8. 查询优化过程

关于 Calcite 的查询计划器有很多巧妙的设计，但在这里我们不过多的赘述。最巧妙的设计是给计划规则的你减轻了负担。

首先，Calcite 不会按照指定的顺序触发规则。查询优化过程会执行分支树的众多分支，就像下棋程序检查所有可能的走法序列一样。如果规则 A 和 B 都匹配了查询操作树的给定部分，则 Calcite 可以同时触发这两个规则；其次，Calcite 基于成本在多个计划中进行选择，但成本模型并不能阻止规则的触发。

许多优化器都有线性优化方案。如上所述，在面对规则 A 和规则 B 的选择时，优化器需要立即做出选择。它可能有诸如将规则 A 应用于整棵树，然后再将规则 B 应用于整棵树的策略，或者基于成本的策略，应用代价最小的规则。Calcite 不需要进行这样的妥协。这使得组合各种规则集合变得简单。如果你想要将识别物化视图的规则与从 CSV 和 JDBC 数据源系统读取数据的规则结合起来，你只要将所有规则的集合提供给 Calcite 并告诉它去执行即可。

Calcite 会使用成本模型。成本模型决定了最终使用哪个计划，有时会剪枝搜索树以防止搜索空间爆炸，但它从不强迫你在规则 A 和规则 B 之间进行选择。这点很重要，因为它避免了在搜索空间中陷入局部最小值，而实际上全局不是最优的。

此外，如你所想，成本模型是可插拔的，它所基于的表和查询操作统计也是可插拔的，但这可以留待以后讨论。

## 9. JDBC 适配器

JDBC 适配器将 JDBC 数据源中的 Schema 与 Calcite Schema 进行映射。如下所示，`FOODMART` 模式 Schema 从 MySQL 中的 `foodmart` 数据库读取数据：
```json
{
  version: '1.0',
  defaultSchema: 'FOODMART',
  schemas: [
    {
      name: 'FOODMART',
      type: 'custom',
      factory: 'org.apache.calcite.adapter.jdbc.JdbcSchema$Factory',
      operand: {
        jdbcDriver: 'com.mysql.jdbc.Driver',
        jdbcUrl: 'jdbc:mysql://localhost/foodmart',
        jdbcUser: 'foodmart',
        jdbcPassword: 'foodmart'
      }
    }
  ]
}
```
> 使用过 Mondrian OLAP 引擎的人应该对 FoodMart 数据库很熟悉，因为它是 Mondrian 的主要测试数据集。要加载数据集，请遵循 [Mondrian 安装说明](https://mondrian.pentaho.com/documentation/installation.php#2_Set_up_test_data) 进行安装。

JDBC 适配器将尽可能多的处理下推到数据源系统，同时转换语法、数据类型和内置函数。如果一个 Calcite 查询基于来自单个 JDBC 数据库的表，原则上整个查询都应该转到该数据库。如果表来自多个 JDBC 数据源，或者 JDBC 和非 JDBC 的混合，Calcite 将使用最有效的分布式查询方法。

## 10. 克隆 JDBC 适配器

克隆 JDBC 适配器会创建一个混合数据库。数据来自 JDBC 数据库，但在第一次访问每个表时会将数据读入内存表。Calcite 基于这些内存表获取查询结果，内存表实际上是数据库的缓存。如下所示模型从 MySQL `foodmart` 数据库读取表数据：
```json
{
  version: '1.0',
  defaultSchema: 'FOODMART_CLONE',
  schemas: [
    {
      name: 'FOODMART_CLONE',
      type: 'custom',
      factory: 'org.apache.calcite.adapter.clone.CloneSchema$Factory',
      operand: {
        jdbcDriver: 'com.mysql.jdbc.Driver',
        jdbcUrl: 'jdbc:mysql://localhost/foodmart',
        jdbcUser: 'foodmart',
        jdbcPassword: 'foodmart'
      }
    }
  ]
}
```
另一个技巧是在现有模式 Schema 之上构建克隆模式 Schema。你可以使用 source 属性来引用模型中之前定义的模式 Schema，就像下面这样：
```json
{
  version: '1.0',
  defaultSchema: 'FOODMART_CLONE',
  schemas: [
    {
      name: 'FOODMART',
      type: 'custom',
      factory: 'org.apache.calcite.adapter.jdbc.JdbcSchema$Factory',
      operand: {
        jdbcDriver: 'com.mysql.jdbc.Driver',
        jdbcUrl: 'jdbc:mysql://localhost/foodmart',
        jdbcUser: 'foodmart',
        jdbcPassword: 'foodmart'
      }
    },
    {
      name: 'FOODMART_CLONE',
      type: 'custom',
      factory: 'org.apache.calcite.adapter.clone.CloneSchema$Factory',
      operand: {
        source: 'FOODMART'
      }
    }
  ]
}
```
您可以使用这种方法在任何类型的模式 Schema 上进行克隆，而不仅仅是 JDBC 类型。克隆适配器并不是万能的。我们计划开发更复杂的缓存策略，以及更完整和更有效的内存表实现，但现在克隆 JDBC 适配器展示了什么是可行的，并允许我们去尝试初始实现。


> 原文: [Tutorial](https://calcite.apache.org/docs/tutorial.html)
